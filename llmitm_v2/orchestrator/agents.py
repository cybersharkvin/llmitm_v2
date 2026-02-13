"""Agent factories for the 2-agent architecture.

Two agent types:
- ProgrammaticAgent: Uses code_execution sandbox + mitmdump tool. Agent writes Python
  that calls `await mitmdump(...)`, intermediate results stay in sandbox (not in context).
- SimpleAgent: Single client.messages.parse() call — no tools, used for Attack Critic.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import anthropic

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

You understand that effective application security testing REQUIRES:

1. **Understanding What the Application Does**
   - You MUST comprehend the application's purpose, data flows, and user interactions
   - You MUST identify authentication mechanisms, API patterns, and trust boundaries
   - You MUST map the application's state machine: login -> session -> action -> logout

2. **Understanding Developer Assumptions**
   - You MUST identify assumptions predicated on business requirements
   - You MUST recognize implicit developer assumptions about user behavior
   - You MUST discover assumptions embedded in the code through traffic analysis
   - You SHOULD note where server-side validation differs from client-side constraints

3. **Finding Assumption Gaps**
   - You MUST recognize that where these assumptions disagree are usually where serious security lapses exist
   - You SHOULD prioritize testing at trust boundary crossings
   - You SHOULD focus on state transitions and authorization decision points
   - You SHOULD test whether the application enforces what it assumes

4. **Skill-Guided Exploration**
   - You MUST follow the relevant skill guide for your current task phase
   - Use `initial_recon` when you have no prior knowledge of the target
   - Use `lateral_movement` when testing authorization boundaries
   - Use `persistence` when validating findings are reproducible

## Your Tool

You have access to `mitmdump` via code execution. Write Python scripts that call
`await mitmdump("...")` to analyze traffic captures or interact with live targets.

Key benefits of programmatic tool calling:
- You can loop over endpoints, filter results, and summarize — only your final print() enters context
- Use variables, conditions, and data structures to organize your exploration
- Chain multiple mitmdump calls in a single script for efficiency

## Output

Your final output MUST be a structured JSON matching the required schema.
Include specific evidence from your mitmdump analysis for every claim.

{skill_guides}
"""

ATTACK_CRITIC_SYSTEM_PROMPT = """You are an adversarial red team lead reviewing attack plans.

You receive a structured attack plan from a recon agent. You have NO tools and NO access
to the target. You see ONLY the plan JSON.

Your role is to tear the plan apart:

1. **Evidence Quality**: Does each attack opportunity cite specific, concrete evidence?
   Reject vague claims like "might be vulnerable" without response data backing it up.

2. **Feasibility**: Can the proposed ActionGraph steps actually be executed deterministically?
   Reject steps that depend on timing, race conditions, or unpredictable server state.

3. **Not Over-Fitted**: Does the plan test the vulnerability generically, or is it
   hardcoded to one specific response? Reject plans that will break if the target
   changes slightly.

4. **Completeness**: Does the plan follow CAMRO phases (Capture, Analyze, Mutate, Replay, Observe)?
   Each phase must be represented. Reject plans missing any phase.

5. **Determinism**: Will the same inputs produce the same outputs every time?
   Reject plans with non-deterministic success criteria.

6. **Attack Surface Coverage**: Did the recon agent explore enough of the application?
   Flag if only surface-level endpoints were tested.

Be harsh but constructive. Provide specific, actionable feedback.
If the plan is genuinely solid, pass it — don't reject for the sake of rejecting.

Respond with passed (bool) and feedback (string)."""


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
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Response truncated (max_tokens reached)")
        if response.parsed_output is None:
            raise RuntimeError(f"No parsed output (stop_reason={response.stop_reason})")
        return AgentResult(structured_output=response.parsed_output)


class ProgrammaticAgent:
    """Agent using programmatic tool calling (code_execution + custom tools).

    The agent writes Python in Anthropic's sandbox. When it calls await mitmdump(...),
    the sandbox pauses and we handle the tool call on our machine (has network access).
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

        for _ in range(self.max_iterations):
            _check_budget()
            response = self.client.beta.messages.create(
                model=self.model_id,
                betas=self.BETAS,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=messages,
                tools=tools,
                **({"output_format": output_format} if output_format else {}),
            )
            _check_and_log_usage(self.model_id, response.usage)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        handler = self.tool_handlers.get(block.name)
                        if handler:
                            result = handler(**block.input)
                        else:
                            result = f"Unknown tool: {block.name}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                continue

            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
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
    model_id: str = "claude-haiku-4-5-20251001",
    api_key: Optional[str] = None,
) -> ProgrammaticAgent:
    """Create Recon Agent with programmatic tool calling + skill guides.

    The Recon Agent explores targets via code_execution + mitmdump tool.
    Used for both compilation (cold start) and repair (self-repair).

    Args:
        mitm_context: Context string describing the .mitm file path or proxy URL.
                      Appended to system prompt so the agent knows where to find traffic.
        model_id: Anthropic model ID
        api_key: Anthropic API key

    Returns:
        ProgrammaticAgent configured with mitmdump tool and skill guides
    """
    from llmitm_v2.tools.recon_tools import MITMDUMP_TOOL_SCHEMA, handle_mitmdump

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))

    skill_guides = load_skill_guides()
    system_prompt = RECON_SYSTEM_PROMPT.replace("{skill_guides}", skill_guides)
    system_prompt += f"\n\n## Target Context\n\n{mitm_context}"

    return ProgrammaticAgent(
        client=client,
        system_prompt=system_prompt,
        model_id=model_id,
        max_tokens=16384,
        tool_schemas=[MITMDUMP_TOOL_SCHEMA],
        tool_handlers={"mitmdump": handle_mitmdump},
        max_iterations=20,
    )


def create_attack_critic(
    model_id: str = "claude-haiku-4-5-20251001",
    api_key: Optional[str] = None,
) -> SimpleAgent:
    """Create Attack Critic — adversarial validator with no tools.

    Reviews Recon Agent's structured output and validates feasibility,
    evidence quality, and determinism.

    Returns:
        SimpleAgent for attack plan validation
    """
    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))
    return SimpleAgent(client, ATTACK_CRITIC_SYSTEM_PROMPT, model_id, 4096)


