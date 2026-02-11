"""Shell command handler using subprocess."""

import os
import re
import subprocess

from llmitm_v2.handlers.base import StepHandler
from llmitm_v2.models.context import ExecutionContext, StepResult
from llmitm_v2.models.step import Step


class ShellCommandHandler(StepHandler):
    """Executes shell commands via subprocess."""

    def execute(self, step: Step, context: ExecutionContext) -> StepResult:
        timeout = step.parameters.get("timeout", 120)
        env = {**os.environ, **step.parameters.get("env", {})}
        cwd = step.parameters.get("cwd")

        try:
            result = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                timeout=timeout,
                env=env,
                cwd=cwd,
            )
            stdout = result.stdout.decode()
            stderr = result.stderr.decode()
            matched = bool(step.success_criteria and re.search(step.success_criteria, stdout))
            return StepResult(
                stdout=stdout,
                stderr=stderr,
                status_code=result.returncode,
                success_criteria_matched=matched,
            )
        except subprocess.TimeoutExpired as exc:
            return StepResult(stderr=f"Timeout after {timeout}s: {exc}", status_code=-1)
