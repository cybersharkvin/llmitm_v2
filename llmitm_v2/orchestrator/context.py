"""Context assembly for LLM reasoning phases.

Builds minimal, phase-specific prompts. Two functions:
- assemble_recon_context(): For Recon Agent (cold start compilation)
- assemble_repair_context(): For Recon Agent (self-repair at failure point)
"""

from llmitm_v2.models import Step


def assemble_recon_context(mitm_file: str = "", proxy_url: str = "") -> str:
    """Build initial prompt for the Recon Agent.

    Works for both file mode (.mitm capture) and live mode (proxy URL).
    The agent uses mitmdump to analyze the capture or interact with the live target.

    Args:
        mitm_file: Path to .mitm capture file (file mode)
        proxy_url: Live proxy URL (live mode)

    Returns:
        Formatted prompt string for Recon Agent
    """
    if mitm_file:
        return f"""You have a pre-recorded traffic capture at: {mitm_file}

TASK:
Analyze this capture using mitmdump to discover:
1. Technology stack (frameworks, servers, languages)
2. Authentication model (JWT, cookies, API keys, etc.)
3. API endpoints and their behavior
4. Potential attack opportunities (IDOR, auth bypass, injection, etc.)

Start by reading all flows:
```python
overview = await mitmdump("-nr {mitm_file} --flow-detail 1")
print(overview)
```

Then drill into specific endpoints with --flow-detail 3 for full request/response bodies.

Follow the initial_recon skill guide methodology. For each potential vulnerability,
validate it using the persistence skill guide before including it in your plan.

Your output MUST be a valid ActionGraph with CAMRO phases targeting the highest-confidence
vulnerability you discover."""

    if proxy_url:
        return f"""You have a live target accessible through a reverse proxy at: {proxy_url}

TASK:
Actively explore this web application to discover:
1. Technology stack (frameworks, servers, languages)
2. Authentication model (JWT, cookies, API keys, etc.)
3. API endpoints and their behavior
4. Potential attack opportunities (IDOR, auth bypass, injection, etc.)

You can capture live traffic with:
```python
# Capture traffic to a file for later analysis
result = await mitmdump("-m reverse:{proxy_url} -w capture.mitm -p 18080")
```

Or send requests directly through the proxy and analyze responses.

Follow the initial_recon skill guide methodology. For each potential vulnerability,
validate it using the persistence skill guide before including it in your plan.

Your output MUST be a valid ActionGraph with CAMRO phases targeting the highest-confidence
vulnerability you discover."""

    return "ERROR: No mitm_file or proxy_url provided."


def assemble_repair_context(
    failed_step: Step, error_log: str, execution_history: list[str],
    mitm_file: str = "", proxy_url: str = "",
) -> str:
    """Assemble context for Recon Agent to diagnose and repair a failed step.

    Args:
        failed_step: Step that failed
        error_log: Error message or status output
        execution_history: Previous step outputs
        mitm_file: Path to .mitm capture file (file mode)
        proxy_url: Live proxy URL (live mode)

    Returns:
        Formatted prompt string for Recon Agent (structured output: RepairDiagnosis)
    """
    max_error_chars = 2000
    truncated_error = error_log[:max_error_chars]
    if len(error_log) > max_error_chars:
        truncated_error += "\n[... truncated ...]"

    recent_outputs = "\n".join(execution_history[:3]) if execution_history else "(no previous steps)"

    target_context = ""
    if mitm_file:
        target_context = f"Traffic capture available at: {mitm_file}"
    elif proxy_url:
        target_context = f"Live target accessible at: {proxy_url}"

    return f"""You are diagnosing a failed step in a vulnerability test.

FAILED STEP:
- Phase: {failed_step.phase}
- Type: {failed_step.type}
- Command: {failed_step.command}
- Parameters: {failed_step.parameters}

ERROR OUTPUT:
{truncated_error}

RECENT EXECUTION HISTORY (last 3 steps):
{recent_outputs}

{target_context}

TASK:
Classify the failure and suggest a repair.

You may use mitmdump to investigate the target's current state if needed.

Respond with:
- failure_type: One of 'transient_recoverable', 'transient_unrecoverable', or 'systemic'
- diagnosis: Brief explanation of what went wrong
- suggested_fix: If systemic, provide the COMPLETE replacement shell command.
  IMPORTANT: The suggested_fix must be a fully self-contained, executable command.
  It must include ALL variable assignments (e.g., TOKEN=$(cat /tmp/file.txt) && curl ...).
  Do NOT reference undefined shell variables. Do NOT include prose or explanation.
  The command replaces the failed step's command field exactly."""
