"""Abstract base class for step handlers."""

from abc import ABC, abstractmethod

from llmitm_v2.models.context import ExecutionContext, StepResult
from llmitm_v2.models.step import Step


class StepHandler(ABC):
    """Base class for all step handlers. Dispatch by StepType."""

    @abstractmethod
    def execute(self, step: Step, context: ExecutionContext) -> StepResult:
        """Execute a step and return a result."""
