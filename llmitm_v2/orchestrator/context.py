"""Context assembly for LLM reasoning phases.

Builds minimal, phase-specific prompts without fetching graph data.
Graph queries are performed by LLM via tools, not context assembly.
"""

from llmitm_v2.models import Fingerprint, Step
from llmitm_v2.models.recon import ReconReport


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
Classify the failure and suggest a repair.

Respond with:
- failure_type: One of 'transient_recoverable', 'transient_unrecoverable', or 'systemic'
- diagnosis: Brief explanation of what went wrong
- suggested_fix: If systemic, provide the COMPLETE replacement shell command.
  IMPORTANT: The suggested_fix must be a fully self-contained, executable command.
  It must include ALL variable assignments (e.g., TOKEN=$(cat /tmp/file.txt) && curl ...).
  Do NOT reference undefined shell variables. Do NOT include prose or explanation.
  The command replaces the failed step's command field exactly."""


def assemble_recon_context(target_url: str) -> str:
    """Build initial prompt for the recon agent.

    Contains target URL and instructions. Used as the first prompt in the recon/critic loop.
    On retry, launcher appends critic feedback to this string.

    Args:
        target_url: Base URL of the target application

    Returns:
        Formatted prompt string for Recon LLM
    """
    return f"""TARGET APPLICATION: {target_url}

TASK:
Actively explore this web application to discover its technology stack, authentication model,
API endpoints, and potential attack opportunities.

Start with common entry points (/, /api/, /rest/, /graphql, /admin, /swagger, health endpoints)
and follow links/paths discovered in responses. Identify the tech stack from response headers
(X-Powered-By, Server, etc.) and error messages.

For each endpoint you discover, record:
- The HTTP method and path
- The response status code
- Whether authentication is required
- Any parameters discovered

For each potential vulnerability, provide:
- The specific endpoint affected
- The vulnerability type (IDOR, auth_bypass, injection, etc.)
- Concrete evidence from your tool calls
- A suggested attack approach to confirm it
- Your confidence level based on evidence strength

Output your findings as a valid JSON structure matching the ReconReport schema."""


def assemble_compilation_context_from_recon(recon_report: ReconReport) -> str:
    """Build compilation context from a ReconReport instead of raw fingerprint + traffic.

    Includes attack_opportunities so the actor agent knows what vulns to target.
    Replaces assemble_compilation_context() when capture_mode=live.

    Args:
        recon_report: Validated ReconReport from the recon agent

    Returns:
        Formatted prompt string for Actor LLM
    """
    # Format attack opportunities
    opportunities = []
    for opp in recon_report.attack_opportunities:
        opportunities.append(
            f"  - {opp.vulnerability_type} at {opp.endpoint} "
            f"(confidence: {opp.confidence:.1f}): {opp.evidence}"
        )
    opportunities_text = "\n".join(opportunities) if opportunities else "  (none identified)"

    # Format discovered endpoints
    endpoints = []
    for ep in recon_report.endpoints_discovered[:20]:  # Limit to 20
        endpoints.append(f"  - {ep.method} {ep.path} → {ep.status_code} ({ep.response_summary})")
    endpoints_text = "\n".join(endpoints) if endpoints else "  (none discovered)"

    # Truncate traffic log
    max_log_chars = 4000
    traffic = recon_report.traffic_log
    if len(traffic) > max_log_chars:
        traffic = traffic[:max_log_chars] + "\n[... truncated ...]"

    return f"""You are an expert at generating vulnerability test scenarios.

TARGET FINGERPRINT:
- Tech Stack: {recon_report.tech_stack}
- Auth Model: {recon_report.auth_model}
- Endpoint Pattern: {recon_report.endpoint_pattern}
- Security Signals: {", ".join(recon_report.security_signals)}
- Target URL: {recon_report.target_url}

DISCOVERED ENDPOINTS:
{endpoints_text}

ATTACK OPPORTUNITIES (from recon):
{opportunities_text}

CAPTURED TRAFFIC:
{traffic}

TASK:
Generate an ActionGraph for testing the highest-confidence attack opportunity above.
The ActionGraph should:
1. Follow CAMRO phases: Capture, Analyze, Mutate, Replay, Observe
2. Be deterministic and repeatable
3. Test the specific vulnerability identified in the recon report
4. Include success criteria (regex patterns or HTTP status codes)

Use find_similar_action_graphs to discover similar vulnerabilities tested before.
Use get_repair_history to understand past repair patterns for this fingerprint.

Output your ActionGraph as a valid JSON structure matching the ActionGraph schema."""
