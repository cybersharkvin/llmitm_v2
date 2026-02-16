"""Flask REST + SSE server for interactive orchestrator control."""

import json
import threading
from pathlib import Path
from typing import Literal, Optional

import gevent
from gevent.queue import Queue as GeventQueue

from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from pydantic import BaseModel

from llmitm_v2.debug_logger import set_event_callback
from llmitm_v2.models.events import RunEndEvent

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Module State ──
_clients: set[GeventQueue] = set()
_clients_lock = threading.Lock()
_current_run_thread: Optional[threading.Thread] = None
_stop_requested: threading.Event = threading.Event()
_graph_repo = None  # Injected at startup
_driver = None  # Injected at startup


# ── Pydantic Models ──
class RunRequest(BaseModel):
    target_profile: Literal["juice_shop", "nodegoat", "dvwa"]
    mode: Literal["file", "live"] = "file"
    traffic_file: Optional[str] = None


class BreakRequest(BaseModel):
    target_profile: Literal["juice_shop", "nodegoat", "dvwa"]
    mode: Literal["file", "live"] = "file"


# ── SSE Fan-Out ──
def _push_event(event_type: str, data: dict) -> None:
    """Fan-out: push SSE bytes to every connected client's queue, then yield to hub."""
    sse_msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
    with _clients_lock:
        for q in list(_clients):
            try:
                q.put_nowait(sse_msg)
            except gevent.queue.Full:
                q.get()  # Drop oldest
                q.put_nowait(sse_msg)
    gevent.sleep(0)  # Yield to hub — lets SSE greenlets flush


# ── Helpers ──
def _get_fingerprint(target_profile: str, mode: str):
    """Get fingerprint for a target profile."""
    from llmitm_v2.config import Settings
    from llmitm_v2.target_profiles import get_active_profile
    from llmitm_v2.models import Fingerprint

    settings = Settings(target_profile=target_profile)
    profile = get_active_profile(target_profile)

    if mode == "live":
        from llmitm_v2.capture.launcher import quick_fingerprint
        fp = quick_fingerprint(settings.target_url)
    else:
        from llmitm_v2.capture.launcher import fingerprint_from_mitm
        traffic_path = Path(__file__).parent.parent.parent / f"demo/{target_profile}.mitm"
        fp = fingerprint_from_mitm(str(traffic_path))

    if fp is None:
        fp = Fingerprint(
            tech_stack="Unknown", auth_model="Unknown",
            endpoint_pattern="/", security_signals=[],
        )

    fp.ensure_hash()
    return fp, settings


# ── Orchestrator Thread Wrapper ──
def _run_orchestrator_thread(settings, fp, mitm_file: str, proxy_url: str) -> None:
    """Background thread that runs orchestrator and emits SSE events."""
    global _current_run_thread
    try:
        from llmitm_v2.orchestrator.agents import set_token_budget
        from llmitm_v2.debug_logger import init_debug_logging, write_summary
        from llmitm_v2.orchestrator import Orchestrator

        set_token_budget(settings.max_token_budget)
        init_debug_logging()

        orchestrator = Orchestrator(_graph_repo, settings)
        result = orchestrator.run(fp, mitm_file=mitm_file, proxy_url=proxy_url)

        write_summary(
            path=result.path,
            compiled=result.compiled,
            repaired=result.repaired,
            success=result.execution.success if result.execution else None,
            steps_executed=result.execution.steps_executed if result.execution else 0,
            findings_count=len(result.execution.findings) if result.execution else 0,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Orchestrator thread failed: %s", e)
        error_event = RunEndEvent(
            success=False, findings_count=0, path="error",
            repaired=False, steps_executed=0,
        )
        _push_event("run_end", error_event.model_dump(mode="json"))
    finally:
        _current_run_thread = None


# ── REST Endpoints ──
@app.route("/run", methods=["POST"])
def api_run():
    """Trigger orchestrator.run() in background thread."""
    global _current_run_thread

    if _current_run_thread is not None and _current_run_thread.is_alive():
        return jsonify({"status": "error", "message": "Run already in progress"}), 409

    try:
        req = RunRequest(**request.json)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    fp, settings = _get_fingerprint(req.target_profile, req.mode)

    if req.traffic_file:
        settings.traffic_file = req.traffic_file
    else:
        settings.traffic_file = f"demo/{req.target_profile}.mitm"

    mitm_file = ""
    if req.mode == "file":
        mitm_file = str(Path(__file__).parent.parent.parent / settings.traffic_file)

    _current_run_thread = threading.Thread(
        target=_run_orchestrator_thread,
        args=(settings, fp, mitm_file, ""),
        daemon=True,
    )
    _current_run_thread.start()

    return jsonify({"status": "started", "fingerprint_hash": fp.hash})


@app.route("/stop", methods=["POST"])
def api_stop():
    """Stop current orchestrator run (graceful)."""
    global _current_run_thread

    if _current_run_thread is None or not _current_run_thread.is_alive():
        return jsonify({"status": "not_running"})

    _stop_requested.set()
    _current_run_thread.join(timeout=5)
    _current_run_thread = None
    _stop_requested.clear()

    return jsonify({"status": "stopped"})


@app.route("/break", methods=["POST"])
def api_break():
    """Corrupt the most recent ActionGraph to trigger self-repair."""
    try:
        req = BreakRequest(**request.json)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    fp, _ = _get_fingerprint(req.target_profile, req.mode)

    try:
        _graph_repo.corrupt_action_graph(fp.hash)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404

    return jsonify({"status": "broken"})


@app.route("/reset", methods=["POST"])
def api_reset():
    """Wipe Neo4j data and recreate schema."""
    _graph_repo.reset_all()
    return jsonify({"status": "reset"})


@app.route("/events")
def events() -> Response:
    """SSE endpoint. Each client gets its own GeventQueue (fan-out)."""
    def stream():
        q: GeventQueue = GeventQueue(maxsize=1000)
        with _clients_lock:
            _clients.add(q)
        try:
            yield b"event: connected\ndata: {}\n\n"
            while True:
                try:
                    msg = q.get(timeout=15)
                    yield msg
                except gevent.queue.Empty:
                    yield b": keepalive\n\n"
        finally:
            with _clients_lock:
                _clients.discard(q)

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        direct_passthrough=True,
    )


@app.route("/health")
def health():
    """Health check."""
    return jsonify({"status": "ok"})


# ── Startup ──
def start_monitor_server(port: int = 5001, driver=None, graph_repo=None) -> threading.Thread:
    """Start Flask in a background thread with injected dependencies."""
    global _graph_repo, _driver
    _graph_repo = graph_repo
    _driver = driver

    set_event_callback(_push_event)

    t = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False),
        daemon=True,
    )
    t.start()
    return t
