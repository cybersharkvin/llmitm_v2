"""mitmproxy addon for passive traffic capture.

Records all HTTP flows passing through the proxy. The recon agent's HTTP tool
sends requests through the proxy; this addon captures everything silently.

Usage: mitmdump -s addon.py ...
"""

from mitmproxy import http


class LLMitMCaptureAddon:
    """Captures request/response pairs flowing through mitmproxy."""

    def __init__(self):
        self.flows = []

    def response(self, flow: http.HTTPFlow) -> None:
        """Capture request + response after both sides complete."""
        self.flows.append({
            "request_method": flow.request.method,
            "request_path": flow.request.path,
            "request_headers": dict(flow.request.headers),
            "request_body": flow.request.get_text(strict=False) or "",
            "response_status_code": flow.response.status_code,
            "response_headers": dict(flow.response.headers),
            "response_body": flow.response.get_text(strict=False) or "",
        })

    def done(self):
        """On shutdown, dump all flows as JSON to stdout."""
        import json
        import sys

        json.dump(self.flows, sys.stdout)


addons = [LLMitMCaptureAddon()]
