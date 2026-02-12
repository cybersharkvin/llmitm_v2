"""Agent factories for compilation and validation.

Both agents are created via Strands SDK. Actor is used for ActionGraph compilation
and RepairDiagnosis generation (via per-call structured_output_model override).
Critic validates ActionGraphs without tools.
"""

import os
from typing import Any, Optional

try:
    from strands import Agent
    from strands.agent import NullConversationManager
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
from llmitm_v2.tools.recon_tools import ReconTools


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
    model_id: str = "claude-haiku-4-5-20251001",
    api_key: Optional[str] = None,
) -> Any:
    """Create Actor agent for compilation and repair.

    The same agent is used for both tasks via per-call structured_output_model override:
    - For ActionGraph compilation: agent(..., structured_output_model=ActionGraph)
    - For failure repair: agent(..., structured_output_model=RepairDiagnosis)

    Args:
        graph_repo: GraphRepository for graph queries
        embed_model: Embedding model (sentence-transformers). Lazy-loaded if None.
        model_id: Anthropic model ID (default: claude-haiku-4-5-20251001).

    Returns:
        Strands Agent configured for graph-aware reasoning
    """
    # Initialize AnthropicModel
    model = AnthropicModel(
        model_id=model_id,
        client_args={"api_key": api_key or os.environ.get("ANTHROPIC_API_KEY", "")},
        max_tokens=16384,
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
        callback_handler=None,
    )


def create_critic_agent(
    model_id: str = "claude-haiku-4-5-20251001",
    api_key: Optional[str] = None,
) -> Any:
    """Create Critic agent for validation (no tools).

    Returns:
        Strands Agent for ActionGraph validation
    """
    # Initialize AnthropicModel
    model = AnthropicModel(
        model_id=model_id,
        client_args={"api_key": api_key or os.environ.get("ANTHROPIC_API_KEY", "")},
        max_tokens=4096,
    )

    # Return agent without tools (validation only)
    return Agent(
        model=model,
        system_prompt=CRITIC_SYSTEM_PROMPT,
        conversation_manager=NullConversationManager(),
        callback_handler=None,
    )


# Recon system prompts
RECON_SYSTEM_PROMPT = """You are an expert recon agent for web application security testing.

You MUST actively explore a target application and discover:
1. Technology stack (frameworks, servers, languages)
2. Authentication model (JWT, cookies, API keys, etc.)
3. API endpoints and their behavior
4. Potential attack opportunities (IDOR, auth bypass, injection, etc.)

You have access to http_request and shell_command tools.

You MUST:
- Hit common endpoints (/, /api/, /rest/, /graphql, /admin, /swagger, etc.)
- Inspect response headers for tech stack clues (X-Powered-By, Server, etc.)
- Record which tool call produced each discovery (tool_context field)

You SHOULD:
- Try different HTTP methods on discovered endpoints
- Attempt unauthenticated access to protected resources
- Look for information disclosure in error responses
- Try default/common credentials on login endpoints
- Explore paths revealed in response bodies (links, redirects, error messages)

You MUST NOT:
- Guess or fabricate observations not directly returned by your tools
- Report an AttackOpportunity without citing specific tool output as evidence
- Leave tech_stack or auth_model as "Unknown" if any response headers were observed

You MAY use shell_command for advanced recon (curl with special flags, DNS lookups, etc.)
when http_request is insufficient.

Every request you make is captured by the proxy for evidence collection.

Your output MUST conform exactly to the ReconReport JSON schema."""

RECON_CRITIC_SYSTEM_PROMPT = """You are an independent validator for reconnaissance reports.

You will receive a ReconReport as JSON. You have NO access to the raw traffic, NO tools,
and NO context beyond this JSON.

You MUST:
- Verify each AttackOpportunity's evidence logically supports its vulnerability_type
- Verify tech_stack and auth_model claims are supported by specific endpoint observations
- Flag any opportunity where evidence could have multiple benign explanations
- Check that tool_context fields reference plausible tool calls

You SHOULD:
- Identify areas the recon agent missed (e.g., no auth probing, no error disclosure checks)
- Note if confidence scores seem inflated relative to the evidence strength

You MUST NOT:
- Invent new attack opportunities (you have no tools)
- Accept claims at face value without checking the cited evidence
- Pass a report where any AttackOpportunity lacks concrete tool_context

Your output MUST conform exactly to the ReconCriticFeedback JSON schema."""


def create_recon_agent(
    proxy_url: str,
    model_id: str = "claude-haiku-4-5-20251001",
    api_key: Optional[str] = None,
) -> Any:
    """Create recon agent with HTTP + shell tools routed through mitmproxy.

    Default: Haiku for dev/testing (cheap). Switch to Opus for production/demo.
    All models are base (non-thinking). No extended thinking / reasoning tokens.

    Invocation: result = agent(prompt, structured_output_model=ReconReport)
    Access: result.structured_output -> validated ReconReport
    """
    recon_tools = ReconTools(proxy_url)
    model = AnthropicModel(
        model_id=model_id,
        client_args={"api_key": api_key or os.environ.get("ANTHROPIC_API_KEY", "")},
        max_tokens=16384,
    )
    return Agent(
        model=model,
        system_prompt=RECON_SYSTEM_PROMPT,
        tools=[recon_tools.http_request, recon_tools.shell_command],
        conversation_manager=NullConversationManager(),
        tool_executor=SequentialToolExecutor(),
        callback_handler=None,
    )


def create_recon_critic_agent(
    model_id: str = "claude-haiku-4-5-20251001",
    api_key: Optional[str] = None,
) -> Any:
    """Create recon critic (no tools). Validates ReconReport JSON only.

    Default: Haiku for dev/testing. Switch to Opus for production/demo.
    All models are base (non-thinking). No extended thinking / reasoning tokens.

    Invocation: result = agent(report.model_dump_json(), structured_output_model=ReconCriticFeedback)
    Access: result.structured_output -> validated ReconCriticFeedback
    """
    model = AnthropicModel(
        model_id=model_id,
        client_args={"api_key": api_key or os.environ.get("ANTHROPIC_API_KEY", "")},
        max_tokens=4096,
    )
    return Agent(
        model=model,
        system_prompt=RECON_CRITIC_SYSTEM_PROMPT,
        conversation_manager=NullConversationManager(),
        callback_handler=None,
    )
