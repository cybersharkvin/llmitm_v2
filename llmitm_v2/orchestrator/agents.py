"""Agent factories for compilation and validation.

Both agents are created via Strands SDK. Actor is used for ActionGraph compilation
and RepairDiagnosis generation (via per-call structured_output_model override).
Critic validates ActionGraphs without tools.
"""

import os
from typing import Any, Optional

try:
    from strands import Agent
    from strands.conversation import NullConversationManager
    from strands.models.anthropic import AnthropicModel
    from strands.tools.executors import SequentialToolExecutor
except ImportError:
    # Graceful fallback when Strands is not available
    Agent = None  # type: ignore
    NullConversationManager = None  # type: ignore
    AnthropicModel = None  # type: ignore
    SequentialToolExecutor = None  # type: ignore

from llmitm_v2.repository import GraphRepository
from llmitm_v2.tools import GraphTools


# System prompts
ACTOR_SYSTEM_PROMPT = """You are an expert vulnerability researcher and test engineer.

Your role is to either:
1. COMPILE: Generate ActionGraphs for testing vulnerabilities in web applications
2. REPAIR: Diagnose and repair failed steps in ActionGraphs

For COMPILATION:
- Use find_similar_action_graphs to discover what vulnerabilities have been tested before
- Reference past patterns but generate novel test sequences
- Follow CAMRO phases: Capture (traffic), Analyze (patterns), Mutate (payloads),
  Replay (execute), Observe (validate)
- Include success_criteria (regex patterns or HTTP status codes)
- Be specific about vulnerability type and testing strategy

For REPAIR:
- Use get_repair_history to understand past repair patterns
- Classify failure into tiers: transient_recoverable, transient_unrecoverable, systemic
- For systemic failures, suggest specific command or parameter changes
- Focus on root cause, not just working around symptoms

Always output valid JSON structures matching the required schema.
Think step-by-step about what you're testing and why."""

CRITIC_SYSTEM_PROMPT = """You are a quality assurance expert for vulnerability test automation.

Your role is to validate ActionGraphs for:
1. **Feasibility**: Can the steps be executed with standard tools (HTTP, regex)?
2. **Determinism**: Will the graph produce consistent results across runs?
3. **Not Over-Fitted**: Does it test the vulnerability generically, not just this instance?
4. **Completeness**: Does it follow the full CAMRO cycle?

Respond with:
- passed: true if the graph passes all criteria, false otherwise
- feedback: Specific, actionable feedback for improvement

Be strict but fair. Even good graphs often need one iteration."""


def create_actor_agent(
    graph_repo: GraphRepository,
    embed_model: Optional[Any] = None,
) -> Any:
    """Create Actor agent for compilation and repair.

    The same agent is used for both tasks via per-call structured_output_model override:
    - For ActionGraph compilation: agent(..., structured_output_model=ActionGraph)
    - For failure repair: agent(..., structured_output_model=RepairDiagnosis)

    Args:
        graph_repo: GraphRepository for graph queries
        embed_model: Embedding model (sentence-transformers). Lazy-loaded if None.

    Returns:
        Strands Agent configured for graph-aware reasoning
    """
    # Initialize AnthropicModel
    model = AnthropicModel(
        model_id="claude-sonnet-4-20250514",
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        max_tokens=4096,
    )

    # Initialize tools
    graph_tools = GraphTools(graph_repo, embed_model)

    # Return configured agent
    return Agent(
        model=model,
        system_prompt=ACTOR_SYSTEM_PROMPT,
        tools=[graph_tools.find_similar_action_graphs, graph_tools.get_repair_history],
        conversation_manager=NullConversationManager(),
        tool_executor=SequentialToolExecutor(),
    )


def create_critic_agent() -> Any:
    """Create Critic agent for validation (no tools).

    Returns:
        Strands Agent for ActionGraph validation
    """
    # Initialize AnthropicModel
    model = AnthropicModel(
        model_id="claude-sonnet-4-20250514",
        client_args={"api_key": os.environ.get("ANTHROPIC_API_KEY", "")},
        max_tokens=1024,
    )

    # Return agent without tools (validation only)
    return Agent(
        model=model,
        system_prompt=CRITIC_SYSTEM_PROMPT,
        conversation_manager=NullConversationManager(),
    )
