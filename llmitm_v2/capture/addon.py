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

        # Write all flows to file on Docker volume mount so host can read
        self._write_flows_to_file()

    def _write_flows_to_file(self) -> None:
        """Write current flows list to /capture/flows.json (mounted volume)."""
        import json
        from pathlib import Path

        try:
            Path("/capture/flows.json").write_text(json.dumps(self.flows))
        except Exception as e:
            # Silently fail if can't write (e.g., not in Docker or no mount)
            pass

    def done(self):
        """On shutdown, ensure all flows are written to file."""
        self._write_flows_to_file()


addons = [LLMitMCaptureAddon()]
