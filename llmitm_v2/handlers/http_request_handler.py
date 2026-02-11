"""HTTP request handler using httpx."""

import re

import httpx

from llmitm_v2.handlers.base import StepHandler
from llmitm_v2.models.context import ExecutionContext, StepResult
from llmitm_v2.models.step import Step


class HTTPRequestHandler(StepHandler):
    """Executes HTTP requests via httpx sync client."""

    def execute(self, step: Step, context: ExecutionContext) -> StepResult:
        url = step.parameters.get("url", step.command)
        if not url.startswith("http"):
            url = context.target_url.rstrip("/") + "/" + url.lstrip("/")

        method = step.parameters.get("method", "GET").upper()
        headers = {**step.parameters.get("headers", {}), **context.session_tokens}
        body = step.parameters.get("body")
        timeout = step.parameters.get("timeout", 30)

        try:
            with httpx.Client(cookies=context.cookies, timeout=timeout) as client:
                response = client.request(method, url, headers=headers, content=body)
                # Extract Set-Cookie values back into context for orchestrator
                for name, value in response.cookies.items():
                    context.cookies[name] = value
                matched = bool(
                    step.success_criteria and re.search(step.success_criteria, response.text)
                )
                return StepResult(
                    stdout=response.text,
                    status_code=response.status_code,
                    success_criteria_matched=matched,
                )
        except Exception as exc:
            return StepResult(stderr=str(exc), status_code=0)
