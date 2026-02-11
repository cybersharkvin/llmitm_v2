"""Application constants and enumerations."""

from enum import Enum


class StepPhase(str, Enum):
    """CAMRO phases: Capture, Analyze, Mutate, Replay, Observe."""

    CAPTURE = "CAPTURE"
    ANALYZE = "ANALYZE"
    MUTATE = "MUTATE"
    REPLAY = "REPLAY"
    OBSERVE = "OBSERVE"


class StepType(str, Enum):
    """Handler dispatch keys for step execution."""

    HTTP_REQUEST = "http_request"
    SHELL_COMMAND = "shell_command"
    REGEX_MATCH = "regex_match"
    JSON_EXTRACT = "json_extract"
    RESPONSE_COMPARE = "response_compare"


class FailureType(str, Enum):
    """Self-repair failure classification tiers."""

    TRANSIENT_RECOVERABLE = "transient_recoverable"
    TRANSIENT_UNRECOVERABLE = "transient_unrecoverable"
    SYSTEMIC = "systemic"


# Constants
MAX_CRITIC_ITERATIONS = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.85
EMBEDDING_DIMENSIONS = 384
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MITM_DEFAULT_PORT = 8080
