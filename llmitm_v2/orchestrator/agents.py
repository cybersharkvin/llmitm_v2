"""Agent factories for the 2-agent architecture.

Two agent types:
- ProgrammaticAgent: Uses code_execution sandbox + recon tools (response_inspect, jwt_decode,
  header_audit, response_diff). Agent writes Python that calls these tools.
- SimpleAgent: Single client.messages.parse() call — no tools, used for Attack Critic.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import anthropic

from llmitm_v2.debug_logger import ToolCallRecord, log_api_call

logger = logging.getLogger(__name__)

# Module-level cumulative token counter
_total_tokens: int = 0
_max_token_budget: int = 50_000


def set_token_budget(budget: int) -> None:
    """Override the default token budget (called from Settings at startup)."""
    global _max_token_budget
    _max_token_budget = budget


def _check_and_log_usage(model_id: str, usage: Any) -> None:
    """Check budget, log usage, increment counter. Shared by both agent types."""
    global _total_tokens
    input_tok = usage.input_tokens
    output_tok = usage.output_tokens
    _total_tokens += input_tok + output_tok
    logger.info(
        "API call: model=%s input=%d output=%d cumulative=%d/%d",
        model_id, input_tok, output_tok, _total_tokens, _max_token_budget,
    )


def _check_budget() -> None:
    """Raise if cumulative token budget is exhausted."""
    if _total_tokens >= _max_token_budget:
        raise RuntimeError(
            f"Token budget exhausted: {_total_tokens}/{_max_token_budget}"
        )


@dataclass
class AgentResult:
    """Thin wrapper for agent output."""
    structured_output: Any


def load_skill_guides() -> str:
    """Read all skill guide markdown files from skills/ directory.

    Returns concatenated markdown string for inclusion in system prompts.
    """
    skills_dir = Path(__file__).parent.parent.parent / "skills"
    if not skills_dir.exists():
        return ""

    parts = []
    for md_file in sorted(skills_dir.glob("*.md")):
        parts.append(f"# Skill Guide: {md_file.stem}\n\n{md_file.read_text()}")

    return "\n\n---\n\n".join(parts)


# System prompts

RECON_SYSTEM_PROMPT = """You are an expert security researcher performing active reconnaissance and attack planning.

## Core Testing Philosophy

You find vulnerabilities by reading developer assumptions from API traffic:

1. **Business Intent**: What was this endpoint supposed to do? Who was it supposed to serve?
2. **Developer Assumptions**: What did the developer assume about who would call this, with what data, in what order?
3. **Code Enforcement**: What does the code actually enforce? Where did the developer forget to check?
4. **The Gap**: Where business intent and code enforcement diverge — that's where vulnerabilities live.

## Your 4 Recon Tools

You have 4 structured tools for analyzing .mitm capture files:

- `response_inspect(mitm_file)` — overview of ALL flows (no filter), or full detail on matching flows (with endpoint_filter regex)
- `jwt_decode(mitm_file)` — find Bearer tokens and decode JWT claims (who is the user, what permissions?)
- `header_audit(mitm_file)` — audit security headers, CORS posture, server info leaks across all flows
- `response_diff(mitm_file, flow_index_a, flow_index_b)` — structural diff of two flows' responses

Call these from code_execution. Example:
```python
overview = await response_inspect(mitm_file="capture.mitm")
print(overview)
```

## Your Output: AttackPlan

Your output prescribes from 5 exploit tools (you do NOT call these — you prescribe them):

| Tool | Tests | Prescribe When |
|------|-------|----------------|
| idor_walk | Resource access across user boundaries | ID-in-URL + different user data returned |
| auth_strip | Endpoints that work without auth | Protected data accessible without token |
| token_swap | Cross-user authorization | User A's token accesses User B's resources |
| namespace_probe | Unprotected admin/internal paths | Admin-prefix endpoints without auth |
| role_tamper | Privilege escalation via body modification | Role/privilege field in request body |

Each AttackOpportunity MUST cite:
- Which recon tool surfaced the evidence
- Specific observation from the tool output
- The suspected assumption gap
- Which exploit tool to run and why

CRITICAL: exploit_target must be a CONCRETE URL path with real IDs from the traffic, not templates.
- CORRECT: "/api/Users/1"
- WRONG: "/api/Users/{id}"

## EFFICIENCY CONSTRAINT

You have a strict token budget. Be efficient:
- Call at most 2 recon tools total (response_inspect + jwt_decode is usually sufficient)
- Do NOT re-call the same tool with the same arguments
- Analyze the results in a single code_execution block, then produce your AttackPlan
- Aim to finish in 3-4 tool turns maximum

{skill_guides}
"""

ATTACK_CRITIC_SYSTEM_PROMPT = """You are an adversarial red team lead refining attack plans.

You receive a JSON AttackPlan from a recon agent. You have NO tools and NO access to the target.

Your job is to produce a REFINED AttackPlan (same schema) that is better than the input:

1. **Remove weak opportunities**: Drop any opportunity with vague evidence or low-confidence reasoning.
   Keep only opportunities backed by specific data from tool output.

2. **Re-tool if needed**: If the wrong exploit tool was prescribed, change it. Only use:
   idor_walk, auth_strip, token_swap, namespace_probe, role_tamper

3. **Reorder by priority**: Put the highest-confidence, highest-impact opportunities first.

4. **Sharpen reasoning**: Tighten the suspected_gap and exploit_reasoning fields.
   The gap must name: business intent → developer assumption → what code doesn't enforce.

5. **Add opportunities if obvious**: If the recon evidence clearly supports an additional attack
   that the agent missed, add it.

Do NOT reject the plan — produce a refined version. If the plan is already excellent,
return it unchanged. Your output MUST be a valid AttackPlan JSON.

IMPORTANT: Return at most 2 opportunities. Keep only the highest-confidence ones.
Fewer, sharper attacks are better than many speculative ones."""


class SimpleAgent:
    """No-tool agent using client.messages.parse() for structured output."""

    def __init__(self, client: anthropic.Anthropic, system_prompt: str, model_id: str, max_tokens: int):
        self.client = client
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.max_tokens = max_tokens

    def __call__(self, prompt: str, structured_output_model: type = None) -> AgentResult:
        _check_budget()
        response = self.client.messages.parse(
            model=self.model_id,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": prompt}],
            output_format=structured_output_model,
        )
        _check_and_log_usage(self.model_id, response.usage)
        log_api_call(agent_type="critic", response=response, messages_len=1, cumulative_tokens=_total_tokens)
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Response truncated (max_tokens reached)")
        if response.parsed_output is None:
            raise RuntimeError(f"No parsed output (stop_reason={response.stop_reason})")
        return AgentResult(structured_output=response.parsed_output)


_MAX_BLOCK_CHARS = 8000  # Cap per content block to prevent context explosion


def _truncate_dict(d: dict, limit: int = _MAX_BLOCK_CHARS) -> None:
    """Recursively truncate string values in a dict."""
    for key, val in d.items():
        if isinstance(val, str) and len(val) > limit:
            d[key] = val[:limit] + "\n...[TRUNCATED]..."
        elif isinstance(val, dict):
            _truncate_dict(val, limit)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    _truncate_dict(item, limit)


def _sanitize_content(content: list) -> list:
    """Sanitize assistant content blocks for re-sending to the API.

    Only modifies blocks that need fixing. Leaves most blocks as raw SDK objects
    (the SDK serializes them correctly). Only intervenes for:
    - tool_use blocks with non-dict input (programmatic calling SDK bug)
    - Blocks with oversized string fields (context explosion prevention)
    """
    out = []
    for block in content:
        # Fix programmatic tool_use: SDK stores input as raw string, API needs dict
        if getattr(block, "type", None) == "tool_use" and not isinstance(block.input, dict):
            out.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": {"command": block.input} if block.input else {},
            })
            continue

        # Truncate oversized blocks (code_execution results can be huge)
        block_size = len(str(block))
        if block_size > _MAX_BLOCK_CHARS:
            d = block.model_dump(exclude={"parsed_output"}) if hasattr(block, "model_dump") else dict(block)
            _truncate_dict(d)
            out.append(d)
        else:
            out.append(block)

    return out


class ProgrammaticAgent:
    """Agent using programmatic tool calling (code_execution + custom tools).

    The agent writes Python in Anthropic's sandbox. When it calls await tool(...),
    the sandbox pauses and we handle the tool call on our machine.
    Intermediate results stay in the sandbox — only final print() output enters context.
    """

    BETAS = ["code-execution-2025-08-25", "advanced-tool-use-2025-11-20"]

    def __init__(
        self,
        client: anthropic.Anthropic,
        system_prompt: str,
        model_id: str,
        max_tokens: int,
        tool_schemas: list[dict],
        tool_handlers: dict[str, Any],
        max_iterations: int = 20,
    ):
        self.client = client
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.tool_schemas = tool_schemas
        self.tool_handlers = tool_handlers
        self.max_iterations = max_iterations

    def __call__(self, prompt: str, structured_output_model: type = None) -> AgentResult:
        _check_budget()

        tools = [
            {"type": "code_execution_20250825", "name": "code_execution"},
            *self.tool_schemas,
        ]

        messages = [{"role": "user", "content": prompt}]
        output_format = None
        if structured_output_model is not None:
            output_format = structured_output_model
        container_id = None

        for _ in range(self.max_iterations):
            _check_budget()
            _tool_calls_this_turn: list[ToolCallRecord] = []
            api_kwargs = dict(
                model=self.model_id,
                betas=self.BETAS,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=messages,
                tools=tools,
            )
            if container_id:
                api_kwargs["container"] = container_id
            if output_format:
                api_kwargs["output_format"] = output_format
                response = self.client.beta.messages.parse(**api_kwargs)
            else:
                response = self.client.beta.messages.create(**api_kwargs)
            # Track container for sandbox continuity
            if hasattr(response, "container") and response.container:
                container_id = response.container.id
            _check_and_log_usage(self.model_id, response.usage)
            log_api_call(
                agent_type="recon", response=response,
                messages_len=len(messages), cumulative_tokens=_total_tokens,
                tool_calls=_tool_calls_this_turn,
            )
            _tool_calls_this_turn = []

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": _sanitize_content(response.content)})
                tool_results = []
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        handler = self.tool_handlers.get(block.name)
                        if handler:
                            inp = block.input
                            result = handler(**inp) if isinstance(inp, dict) else handler(inp)
                        else:
                            result = f"Unknown tool: {block.name}"
                        _tool_calls_this_turn.append(ToolCallRecord(
                            name=block.name, input_preview=str(inp)[:200],
                            result_length=len(str(result)),
                        ))
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": _sanitize_content(response.content)})
                continue

            if response.stop_reason in ("end_turn",):
                parsed = getattr(response, "parsed_output", None)
                if parsed is not None:
                    return AgentResult(structured_output=parsed)
                raise RuntimeError(f"No parsed output (stop_reason={response.stop_reason})")

            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")

        raise RuntimeError(f"ProgrammaticAgent exceeded {self.max_iterations} iterations")


def create_recon_agent(
    mitm_context: str,
    model_id: str = "claude-sonnet-4-5-20250929",
    api_key: Optional[str] = None,
) -> ProgrammaticAgent:
    """Create Recon Agent with programmatic tool calling + skill guides.

    The Recon Agent explores targets via code_execution + 4 recon tools.
    Used for both compilation (cold start) and repair (self-repair).

    Args:
        mitm_context: Context string describing the .mitm file path or proxy URL.
                      Appended to system prompt so the agent knows where to find traffic.
        model_id: Anthropic model ID
        api_key: Anthropic API key

    Returns:
        ProgrammaticAgent configured with recon tools and skill guides
    """
    from llmitm_v2.tools.recon_tools import TOOL_HANDLERS, TOOL_SCHEMAS

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))

    system_prompt = RECON_SYSTEM_PROMPT.replace("{skill_guides}", "")
    system_prompt += f"\n\n## Target Context\n\n{mitm_context}"

    return ProgrammaticAgent(
        client=client,
        system_prompt=system_prompt,
        model_id=model_id,
        max_tokens=16384,
        tool_schemas=TOOL_SCHEMAS,
        tool_handlers=TOOL_HANDLERS,
        max_iterations=8,
    )


def create_attack_critic(
    model_id: str = "claude-sonnet-4-5-20250929",
    api_key: Optional[str] = None,
) -> SimpleAgent:
    """Create Attack Critic — adversarial refiner with no tools.

    Receives AttackPlan JSON and produces a refined AttackPlan (same schema).

    Returns:
        SimpleAgent for attack plan refinement
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))
    return SimpleAgent(client, ATTACK_CRITIC_SYSTEM_PROMPT, model_id, 4096)
