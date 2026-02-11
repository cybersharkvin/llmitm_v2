"""Regex match handler for response validation."""

import re

from llmitm_v2.handlers.base import StepHandler
from llmitm_v2.models.context import ExecutionContext, StepResult
from llmitm_v2.models.step import Step


class RegexMatchHandler(StepHandler):
    """Matches regex patterns against previous step outputs."""

    def execute(self, step: Step, context: ExecutionContext) -> StepResult:
        pattern = step.parameters.get("pattern", step.command)
        source_index = step.parameters.get("source", "last")
        capture_group = step.parameters.get("capture_group", 0)

        if not context.previous_outputs:
            return StepResult(stderr="No previous outputs available")

        if source_index == "last":
            source = context.previous_outputs[-1]
        else:
            source = context.previous_outputs[int(source_index)]

        match = re.search(pattern, source)
        if match:
            return StepResult(stdout=match.group(capture_group), success_criteria_matched=True)
        return StepResult(stdout="", success_criteria_matched=False)
