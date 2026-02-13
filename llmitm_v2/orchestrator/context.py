"""Context assembly for LLM reasoning phases.

Builds minimal, phase-specific prompts. Two functions:
- assemble_recon_context(): Full prompt for Recon Agent (cold start / repair compilation)
- assemble_repair_context(): Enrichment string prepended to recon context on repair
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
) -> str:
    """Build context enrichment string describing a failed execution.

    This string gets prepended to the normal recon context in _compile(),
    so the Recon Agent sees what failed and can account for it.

    Args:
        failed_step: Step that failed
        error_log: Error message or status output
        execution_history: Previous step outputs

    Returns:
        Context enrichment string (not a full prompt)
    """
    max_error_chars = 2000
    truncated_error = error_log[:max_error_chars]
    if len(error_log) > max_error_chars:
        truncated_error += "\n[... truncated ...]"

    recent_outputs = "\n".join(execution_history[:3]) if execution_history else "(no previous steps)"

    return f"""## Previous Execution State

A prior ActionGraph was executed but failed at step {failed_step.order} ({failed_step.phase}, {failed_step.type}).
Command: {failed_step.command}
Parameters: {failed_step.parameters}

Error output:
{truncated_error}

Steps that succeeded before failure:
{recent_outputs}

Account for this failure in your new ActionGraph. The previous approach did not work —
produce a corrected plan that avoids the same issue.

"""
