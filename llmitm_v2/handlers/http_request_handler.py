"""HTTP request handler using httpx."""

import json
import re
from pathlib import Path

import httpx

from llmitm_v2.handlers.base import StepHandler
from llmitm_v2.models.context import ExecutionContext, StepResult
from llmitm_v2.models.step import Step


class HTTPRequestHandler(StepHandler):
    """Executes HTTP requests via httpx sync client."""

    def execute(self, step: Step, context: ExecutionContext) -> StepResult:
        url = step.parameters.get("url", step.parameters.get("path", step.command))
        if not url.startswith("http"):
            url = context.target_url.rstrip("/") + "/" + url.lstrip("/")

        method = step.parameters.get("method", "GET").upper()
        headers = {**step.parameters.get("headers", {}), **context.session_tokens}
        body = step.parameters.get("body")
        timeout = step.parameters.get("timeout", 30)

        skip_cookies = step.parameters.get("skip_cookies", False)
        cookies = {} if skip_cookies else context.cookies

        try:
            with httpx.Client(cookies=cookies, timeout=timeout, follow_redirects=True) as client:
                kwargs = {"headers": headers}
                if isinstance(body, dict):
                    if step.parameters.get("json"):
                        kwargs["json"] = body
                    else:
                        kwargs["data"] = body
                elif body is not None:
                    kwargs["content"] = body
                response = client.request(method, url, **kwargs)
                # Extract Set-Cookie values back into context for orchestrator
                for name, value in response.cookies.items():
                    context.cookies[name] = value
                # Extract auth token from response body if step requests it
                token_path = step.parameters.get("extract_token_path")
                if token_path:
                    try:
                        data = response.json()
                        for key in token_path.split("."):
                            data = data[key]
                        context.session_tokens["Authorization"] = f"Bearer {data}"
                    except Exception:
                        pass
                if step.output_file:
                    tmp_dir = Path(__file__).resolve().parent.parent / "tmp"
                    tmp_dir.mkdir(exist_ok=True)
                    (tmp_dir / Path(step.output_file).name).write_text(response.text)
                matched = bool(
                    step.success_criteria and re.search(step.success_criteria, response.text)
                )
                stderr = ""
                if response.status_code >= 400:
                    stderr = f"HTTP {response.status_code}"
                return StepResult(
                    stdout=response.text,
                    stderr=stderr,
                    status_code=response.status_code,
                    success_criteria_matched=matched,
                )
        except Exception as exc:
            return StepResult(stderr=str(exc), status_code=0)
