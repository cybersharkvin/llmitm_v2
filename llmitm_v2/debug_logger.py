"""Debug logging for agent pipeline. Opt-in via DEBUG_LOGGING=true env var.

Creates debug_logs/<timestamp>/ with per-API-call JSON files and a run summary.
All functions are no-ops when disabled — zero overhead in normal runs.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ContentBlockSummary(BaseModel):
    """Summary of a single content block (text, tool_use, server_tool_use, etc.)."""
    type: str
    name: Optional[str] = None
    length: Optional[int] = None
    input_preview: Optional[str] = None


class ToolCallRecord(BaseModel):
    """Record of a dispatched tool call and its result."""
    name: str
    input_preview: str = ""
    result_length: int = 0


class ApiCallLog(BaseModel):
    """Per-API-call debug record. Written as call_NNN.json."""
    call_number: int
    agent_type: str
    timestamp: str
    request_id: Optional[str] = None
    model: str = ""
    stop_reason: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cumulative_tokens: int = 0
    messages_length: int = 0
    container_id: Optional[str] = None
    content_blocks: list[ContentBlockSummary] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)


class EventLog(BaseModel):
    """Orchestrator milestone event. Written as event_NNN_<type>.json."""
    event_number: int
    event_type: str
    timestamp: str
    data: dict[str, Any] = Field(default_factory=dict)


class RunSummary(BaseModel):
    """End-of-run summary. Written as run_summary.json."""
    run_dir: str
    started_at: str
    finished_at: str
    total_api_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    path: Optional[str] = None
    compiled: bool = False
    repaired: bool = False
    success: Optional[bool] = None
    steps_executed: int = 0
    findings_count: int = 0
    api_calls: list[ApiCallLog] = Field(default_factory=list)
    events: list[EventLog] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Module State
# ---------------------------------------------------------------------------

_run_dir: Optional[Path] = None
_call_counter: int = 0
_event_counter: int = 0
_calls: list[ApiCallLog] = []
_events: list[EventLog] = []
_started_at: str = ""
_event_callback: Optional[object] = None  # Callable[[str, dict[str, Any]], None]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_debug_logging() -> None:
    """Create debug_logs/<timestamp>/ if DEBUG_LOGGING env var is truthy."""
    global _run_dir, _call_counter, _event_counter, _calls, _events, _started_at
    if os.environ.get("DEBUG_LOGGING", "").lower() not in ("1", "true", "yes"):
        return
    _started_at = datetime.now(timezone.utc).isoformat()
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _run_dir = Path("debug_logs") / ts
    _run_dir.mkdir(parents=True, exist_ok=True)
    _call_counter = 0
    _event_counter = 0
    _calls = []
    _events = []


def is_enabled() -> bool:
    return _run_dir is not None


def set_event_callback(callback: object) -> None:
    """Register a callback invoked on every log_event(), independent of DEBUG_LOGGING."""
    global _event_callback
    _event_callback = callback


def log_api_call(
    *,
    agent_type: str,
    response: object,
    messages_len: int,
    cumulative_tokens: int = 0,
    tool_calls: Optional[list[ToolCallRecord]] = None,
) -> None:
    """Extract metadata from API response and write call_NNN.json."""
    if not is_enabled():
        return
    global _call_counter

    usage = getattr(response, "usage", None)
    input_tok = getattr(usage, "input_tokens", 0) if usage else 0
    output_tok = getattr(usage, "output_tokens", 0) if usage else 0

    container = getattr(response, "container", None)
    container_id = getattr(container, "id", None) if container else None

    content_blocks = _summarize_content_blocks(getattr(response, "content", []))

    entry = ApiCallLog(
        call_number=_call_counter,
        agent_type=agent_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=getattr(response, "id", None),
        model=getattr(response, "model", ""),
        stop_reason=getattr(response, "stop_reason", None),
        input_tokens=input_tok,
        output_tokens=output_tok,
        cumulative_tokens=cumulative_tokens,
        messages_length=messages_len,
        container_id=container_id,
        content_blocks=content_blocks,
        tool_calls=tool_calls or [],
    )
    _write_json(f"call_{_call_counter:03d}.json", entry)
    _calls.append(entry)
    _call_counter += 1


def log_event(event_type: str, data: "dict[str, Any] | BaseModel") -> None:
    """Write event_NNN_<type>.json for orchestrator milestones."""
    from pydantic import BaseModel as _BM

    if isinstance(data, _BM):
        data = data.model_dump(mode="json")

    # Invoke callback unconditionally (decoupled from DEBUG_LOGGING)
    if _event_callback is not None:
        _event_callback(event_type, data)

    if not is_enabled():
        return
    global _event_counter

    entry = EventLog(
        event_number=_event_counter,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=data,
    )
    _write_json(f"event_{_event_counter:03d}_{event_type}.json", entry)
    _events.append(entry)
    _event_counter += 1


def write_summary(
    *,
    path: Optional[str] = None,
    compiled: bool = False,
    repaired: bool = False,
    success: Optional[bool] = None,
    steps_executed: int = 0,
    findings_count: int = 0,
) -> None:
    """Write run_summary.json with aggregated stats + all calls/events."""
    if not is_enabled():
        return

    summary = RunSummary(
        run_dir=str(_run_dir),
        started_at=_started_at,
        finished_at=datetime.now(timezone.utc).isoformat(),
        total_api_calls=len(_calls),
        total_input_tokens=sum(c.input_tokens for c in _calls),
        total_output_tokens=sum(c.output_tokens for c in _calls),
        path=path,
        compiled=compiled,
        repaired=repaired,
        success=success,
        steps_executed=steps_executed,
        findings_count=findings_count,
        api_calls=_calls,
        events=_events,
    )
    _write_json("run_summary.json", summary)


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------


def _summarize_content_blocks(content: list) -> list[ContentBlockSummary]:
    """Extract type/name/length from response content blocks."""
    summaries = []
    for block in content or []:
        btype = getattr(block, "type", "unknown")
        name = getattr(block, "name", None)
        length = None
        input_preview = None

        if btype == "text":
            text = getattr(block, "text", "")
            length = len(text)
        elif btype in ("tool_use", "server_tool_use"):
            inp = getattr(block, "input", None)
            if inp is not None:
                input_preview = str(inp)[:200]

        summaries.append(ContentBlockSummary(
            type=btype, name=name, length=length, input_preview=input_preview,
        ))
    return summaries


def _write_json(filename: str, model: BaseModel) -> None:
    """Write a Pydantic model as pretty JSON to _run_dir/filename."""
    if _run_dir is None:
        return
    (_run_dir / filename).write_text(
        json.dumps(model.model_dump(), indent=2, default=str)
    )
