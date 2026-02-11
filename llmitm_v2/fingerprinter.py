"""Rule-based HTTP traffic fingerprinter for target identification."""

import re
from typing import Any

from llmitm_v2.models import Fingerprint


class Fingerprinter:
    """Extract Fingerprint from HTTP traffic using deterministic rules."""

    def fingerprint(self, traffic_log: str) -> Fingerprint:
        """Parse traffic log -> Fingerprint with tech_stack, auth_model, endpoint_pattern, security_signals."""
        requests, responses = self._parse_traffic_log(traffic_log)

        tech_stack = self._extract_tech_stack(responses)
        auth_model = self._extract_auth_model(requests)
        endpoint_pattern = self._extract_endpoint_pattern(requests)
        security_signals = self._extract_security_signals(responses)

        return Fingerprint(
            tech_stack=tech_stack,
            auth_model=auth_model,
            endpoint_pattern=endpoint_pattern,
            security_signals=security_signals,
        )

    @staticmethod
    def _parse_traffic_log(traffic_log: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Parse traffic log text into structured request/response dicts.

        Format: >>> [request] <<< [response]
        """
        requests = []
        responses = []

        # Split on request delimiters
        parts = traffic_log.split(">>>")
        for part in parts[1:]:  # Skip first empty part
            if "<<<" not in part:
                continue

            req_text, resp_text = part.split("<<<", 1)
            requests.append(Fingerprinter._parse_request(req_text.strip()))
            responses.append(Fingerprinter._parse_response(resp_text.strip()))

        return requests, responses

    @staticmethod
    def _parse_request(text: str) -> dict[str, Any]:
        """Parse HTTP request text into dict."""
        lines = text.split("\n")
        if not lines:
            return {}

        # First line: METHOD path HTTP/VERSION
        req_line = lines[0].split()
        method = req_line[0] if req_line else "GET"
        path = req_line[1] if len(req_line) > 1 else "/"

        # Headers
        headers = {}
        body_start = 1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "":
                body_start = i + 1
                break
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip()] = val.strip()

        body = "\n".join(lines[body_start:]).strip()

        return {
            "method": method,
            "path": path,
            "headers": headers,
            "body": body,
        }

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        """Parse HTTP response text into dict."""
        lines = text.split("\n")
        if not lines:
            return {}

        # First line: HTTP/VERSION status
        status_line = lines[0].split()
        status_code = int(status_line[1]) if len(status_line) > 1 else 200

        # Headers
        headers = {}
        body_start = 1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "":
                body_start = i + 1
                break
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip()] = val.strip()

        body = "\n".join(lines[body_start:]).strip()

        return {
            "status_code": status_code,
            "headers": headers,
            "body": body,
        }

    @staticmethod
    def _extract_tech_stack(responses: list[dict[str, Any]]) -> str:
        """Extract tech stack from response headers (X-Powered-By, Server, etc.)."""
        for response in responses:
            headers = response.get("headers", {})
            if "X-Powered-By" in headers:
                return headers["X-Powered-By"]
            if "Server" in headers:
                return headers["Server"]
        return "Unknown"

    @staticmethod
    def _extract_auth_model(requests: list[dict[str, Any]]) -> str:
        """Extract auth model from request headers (Bearer, Basic, Cookie, etc.)."""
        for request in requests:
            headers = request.get("headers", {})
            # Bearer token
            if "Authorization" in headers:
                auth_val = headers["Authorization"]
                if auth_val.startswith("Bearer"):
                    return "JWT Bearer"
                elif auth_val.startswith("Basic"):
                    return "Basic Auth"
                else:
                    return auth_val.split()[0] if auth_val else "Unknown"
            # Cookie-based
            if "Cookie" in headers:
                return "Cookie-based"
        return "Unknown"

    @staticmethod
    def _extract_endpoint_pattern(requests: list[dict[str, Any]]) -> str:
        """Extract most common endpoint prefix (e.g., /api/*, /rest/*)."""
        patterns = {}
        for request in requests:
            path = request.get("path", "/")
            # Get first two path segments
            parts = path.strip("/").split("/")
            if parts and parts[0]:
                prefix = f"/{parts[0]}/*"
                patterns[prefix] = patterns.get(prefix, 0) + 1

        if not patterns:
            return "/"

        # Return most common pattern
        return max(patterns, key=patterns.get)

    @staticmethod
    def _extract_security_signals(responses: list[dict[str, Any]]) -> list[str]:
        """Extract security indicators from response headers."""
        signals = []

        for response in responses:
            headers = response.get("headers", {})

            # CORS
            if "Access-Control-Allow-Origin" in headers:
                val = headers["Access-Control-Allow-Origin"]
                if val == "*":
                    signals.append("CORS permissive")

            # CSP
            if "Content-Security-Policy" not in headers and "Content-Security-Policy-Report-Only" not in headers:
                if not any("CSP" in s for s in signals):
                    signals.append("no CSP")

            # X-Frame-Options
            if "X-Frame-Options" in headers:
                val = headers["X-Frame-Options"]
                if val.upper() == "SAMEORIGIN":
                    signals.append("clickjacking protected")

        return list(set(signals))  # Deduplicate
