"""Context assembly for LLM reasoning phases.

Builds minimal, phase-specific prompts. Two functions:
- assemble_recon_context(): Full prompt for Recon Agent (cold start / repair compilation)
- assemble_repair_context(): Enrichment string prepended to recon context on repair
"""

from llmitm_v2.models import Step


def assemble_recon_context(mitm_file: str = "", proxy_url: str = "") -> str:
    """Build initial prompt for the Recon Agent.

    Works for both file mode (.mitm capture) and live mode (proxy URL).
    The agent uses 4 recon tools to analyze the capture.

    Args:
        mitm_file: Path to .mitm capture file (file mode)
        proxy_url: Live proxy URL (live mode)

    Returns:
        Formatted prompt string for Recon Agent
    """
    if mitm_file:
        return f"""You have a captured traffic file at: {mitm_file}

Use your recon tools to analyze the capture:
- response_inspect: see what endpoints were hit and what came back
- jwt_decode: understand who the authenticated user is and what the token carries
- header_audit: assess the security posture across all endpoints
- response_diff: compare responses between flows to spot behavioral differences

Your job is to read the developer's assumptions from the API design.
Find where business intent diverged from what the code actually enforces.
Each opportunity must cite specific evidence from your tool calls.

Your output is a prioritized attack plan. Each opportunity prescribes an exploit tool:
- idor_walk: enumerate resource IDs with another user's token
- auth_strip: replay requests without authentication
- token_swap: replay User A's request with User B's token
- namespace_probe: probe path namespace for unprotected siblings
- role_tamper: modify role/privilege fields in request body"""

    if proxy_url:
        return f"""You have a live target accessible through a reverse proxy at: {proxy_url}

Use your recon tools to analyze captured traffic.
The capture file will be available at the path specified in the target context.

Your job is to read the developer's assumptions from the API design.
Find where business intent diverged from what the code actually enforces.
Each opportunity must cite specific evidence from your tool calls.

Your output is a prioritized attack plan. Each opportunity prescribes an exploit tool:
- idor_walk: enumerate resource IDs with another user's token
- auth_strip: replay requests without authentication
- token_swap: replay User A's request with User B's token
- namespace_probe: probe path namespace for unprotected siblings
- role_tamper: modify role/privilege fields in request body"""

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

A prior attack plan was executed but failed at step {failed_step.order} ({failed_step.phase}, {failed_step.type}).
Command: {failed_step.command}
Parameters: {failed_step.parameters}

Error output:
{truncated_error}

Steps that succeeded before failure:
{recent_outputs}

Account for this failure in your new attack plan. The previous approach did not work —
produce a corrected plan that avoids the same issue.

"""
