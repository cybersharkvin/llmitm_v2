"""Recon tools for LLM-driven active reconnaissance via mitmproxy.

All HTTP requests route through the mitmproxy reverse proxy so the addon captures everything.
"""

import subprocess

import httpx

try:
    from strands import tool
except ImportError:
    def tool(func):  # type: ignore
        """Stub tool decorator when Strands is not available."""
        return func


class ReconTools:
    """Tools the recon agent uses to explore a target through mitmproxy."""

    def __init__(self, proxy_url: str):
        """Initialize with proxy URL (e.g., http://localhost:8080)."""
        self.proxy_url = proxy_url
        self.client = httpx.Client(timeout=30, verify=False)

    @tool
    def http_request(self, method: str, path: str, headers: dict = None, body: str = "") -> str:
        """Send HTTP request through the proxy. Returns status + headers + body.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: URL path relative to target root (e.g., /api/Users)
            headers: Optional HTTP headers dict
            body: Optional request body string

        Returns:
            Formatted string with STATUS, HEADERS, and BODY sections
        """
        url = self.proxy_url.rstrip("/") + "/" + path.lstrip("/")
        resp = self.client.request(method, url, headers=headers or {}, content=body)
        return f"STATUS: {resp.status_code}\nHEADERS: {dict(resp.headers)}\nBODY: {resp.text[:4000]}"

    @tool
    def shell_command(self, command: str) -> str:
        """Run a shell command (curl, nmap, etc.) for advanced recon.

        Args:
            command: Shell command to execute

        Returns:
            Formatted string with STDOUT and STDERR sections
        """
        result = subprocess.run(
            command, shell=True, capture_output=True, timeout=30,
        )
        return f"STDOUT: {result.stdout.decode()[:4000]}\nSTDERR: {result.stderr.decode()[:1000]}"
