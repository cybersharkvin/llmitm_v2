"""Context assembly for LLM reasoning phases.

Builds minimal, phase-specific prompts without fetching graph data.
Graph queries are performed by LLM via tools, not context assembly.
"""

from llmitm_v2.models import Fingerprint, Step


def assemble_compilation_context(fingerprint: Fingerprint, traffic_log: str) -> str:
    """Assemble static context for ActionGraph compilation.

    Provides target fingerprint characteristics and truncated traffic log.
    LLM discovers similar graphs via find_similar_action_graphs tool.

    Args:
        fingerprint: Target Fingerprint identifying the system
        traffic_log: Captured HTTP traffic (will be truncated if too long)

    Returns:
        Formatted prompt string for Actor LLM
    """
    # Truncate traffic log to reasonable length
    max_log_chars = 4000
    if len(traffic_log) > max_log_chars:
        truncated_log = traffic_log[:max_log_chars] + "\n[... truncated ...]"
    else:
        truncated_log = traffic_log

    return f"""You are an expert at generating vulnerability test scenarios.

TARGET FINGERPRINT:
- Tech Stack: {fingerprint.tech_stack}
- Auth Model: {fingerprint.auth_model}
- Endpoint Pattern: {fingerprint.endpoint_pattern}
- Security Signals: {", ".join(fingerprint.security_signals)}

CAPTURED TRAFFIC:
{truncated_log}

TASK:
Generate an ActionGraph for testing vulnerabilities in this target.
The ActionGraph should:
1. Follow CAMRO phases: Capture, Analyze, Mutate, Replay, Observe
2. Be deterministic and repeatable
3. Test a specific vulnerability type (IDOR, auth bypass, privilege escalation, etc.)
4. Include success criteria (regex patterns or HTTP status codes)

Use find_similar_action_graphs to discover similar vulnerabilities tested before.
Use get_repair_history to understand past repair patterns for this fingerprint.

Output your ActionGraph as a valid JSON structure matching the ActionGraph schema."""


def assemble_repair_context(
    failed_step: Step, error_log: str, execution_history: list[str]
) -> str:
    """Assemble context for LLM-assisted step repair.

    Provides failed step details, error context, and recent execution history.
    LLM discovers repair history via get_repair_history tool.

    Args:
        failed_step: Step that failed
        error_log: Error message or status output (will be truncated)
        execution_history: Previous step outputs (most recent first)

    Returns:
        Formatted prompt string for Actor LLM (structured output: RepairDiagnosis)
    """
    # Truncate error log
    max_error_chars = 2000
    if len(error_log) > max_error_chars:
        truncated_error = error_log[:max_error_chars] + "\n[... truncated ...]"
    else:
        truncated_error = error_log

    # Include last 3 step outputs for context
    recent_outputs = "\n".join(execution_history[:3]) if execution_history else "(no previous steps)"

    return f"""You are a diagnostic expert analyzing a failed step in a vulnerability test.

FAILED STEP:
- Phase: {failed_step.phase}
- Type: {failed_step.type}
- Command: {failed_step.command}
- Parameters: {failed_step.parameters}

ERROR OUTPUT:
{truncated_error}

RECENT EXECUTION HISTORY (last 3 steps):
{recent_outputs}

TASK:
Classify the failure and suggest a repair strategy.

Use get_repair_history to understand how similar failures were repaired before.

Respond with:
- failure_type: One of 'transient_recoverable' (retry immediately), 'transient_unrecoverable' (restart graph), or 'systemic' (needs repair)
- suggested_repair_command: Optional new command or parameters to fix the failure

Consider:
1. Is this a temporary network/load issue? → transient_recoverable
2. Is this an endpoint/session lost? → transient_unrecoverable
3. Does the strategy itself need to change? → systemic"""
