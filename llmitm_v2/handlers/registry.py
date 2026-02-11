"""Handler registry for dispatch by StepType."""

from typing import Dict, Type

from llmitm_v2.constants import StepType
from llmitm_v2.handlers.base import StepHandler
from llmitm_v2.handlers.http_request_handler import HTTPRequestHandler
from llmitm_v2.handlers.regex_match_handler import RegexMatchHandler
from llmitm_v2.handlers.shell_command_handler import ShellCommandHandler

HANDLER_REGISTRY: Dict[StepType, Type[StepHandler]] = {
    StepType.HTTP_REQUEST: HTTPRequestHandler,
    StepType.SHELL_COMMAND: ShellCommandHandler,
    StepType.REGEX_MATCH: RegexMatchHandler,
}


def get_handler(step_type: StepType) -> StepHandler:
    """Instantiate and return a handler for the given step type."""
    if step_type not in HANDLER_REGISTRY:
        raise ValueError(f"No handler registered for step type: {step_type}")
    return HANDLER_REGISTRY[step_type]()
