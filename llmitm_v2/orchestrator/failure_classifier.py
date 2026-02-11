"""Deterministic failure classification for self-repair tier selection."""

from llmitm_v2.constants import FailureType


def classify_failure(error_log: str, status_code: int = 0) -> FailureType:
    """Classify step execution failure into repair tiers.

    Deterministic-first approach: obvious failures handled without LLM.
    Only truly ambiguous cases should return SYSTEMIC (requires LLM diagnosis).

    Args:
        error_log: Error message or log output from failed step
        status_code: HTTP status code (0 if not applicable)

    Returns:
        FailureType: One of TRANSIENT_RECOVERABLE, TRANSIENT_UNRECOVERABLE, SYSTEMIC
    """
    error_lower = error_log.lower()

    # Transient recoverable: retry immediately (network/load issues)
    if status_code in (429, 503):
        return FailureType.TRANSIENT_RECOVERABLE
    if any(word in error_lower for word in ["timeout", "timed out", "connection reset"]):
        return FailureType.TRANSIENT_RECOVERABLE

    # Transient unrecoverable: restart full ActionGraph (session/endpoint lost)
    if status_code in (401, 403, 404):
        return FailureType.TRANSIENT_UNRECOVERABLE
    if any(word in error_lower for word in ["session expired", "unauthorized", "forbidden"]):
        return FailureType.TRANSIENT_UNRECOVERABLE

    # Systemic: requires LLM diagnosis (unknown/ambiguous)
    return FailureType.SYSTEMIC
