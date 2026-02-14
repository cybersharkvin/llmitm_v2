"""Recon tools for the Recon Agent.

4 FlowReader-based tools for analyzing .mitm capture files.
Grammar-enforced via strict tool schemas — agent can only call these.
"""

import base64
import json
import re

from mitmproxy.io import FlowReader


# ── Helpers ──────────────────────────────────────────────────────────


def _read_flows(mitm_file: str) -> list:
    """Read all flows from a .mitm file via FlowReader."""
    flows = []
    with open(mitm_file, "rb") as f:
        reader = FlowReader(f)
        for flow in reader.stream():
            flows.append(flow)
    return flows


def _flow_summary(index: int, flow) -> dict:
    """Extract one-line summary from a flow object."""
    req = flow.request
    resp = flow.response
    has_auth = bool(req.headers.get("Authorization", "") or req.headers.get("Cookie", ""))
    content_type = resp.headers.get("Content-Type", "") if resp else ""
    return {
        "index": index,
        "method": req.method,
        "url": req.pretty_url,
        "status": resp.status_code if resp else None,
        "has_auth": has_auth,
        "content_type": content_type.split(";")[0].strip(),
    }


def _flow_detail(flow, body_limit: int = 4000) -> dict:
    """Extract full structured detail from a flow object."""
    req = flow.request
    resp = flow.response

    req_body = _safe_json(req.content) if req.content else None
    resp_body = _safe_json(resp.content) if resp and resp.content else None

    return {
        "request": {
            "method": req.method,
            "url": req.pretty_url,
            "headers": dict(req.headers),
            "body": req_body,
        },
        "response": {
            "status": resp.status_code if resp else None,
            "headers": dict(resp.headers) if resp else {},
            "body": resp_body,
        },
    }


def _safe_json(body_bytes: bytes | None) -> object:
    """Try to parse body as JSON; fall back to truncated text."""
    if not body_bytes:
        return None
    try:
        return json.loads(body_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        text = body_bytes.decode(errors="replace")[:4000]
        return text


# ── Tool 1: response_inspect ────────────────────────────────────────

RESPONSE_INSPECT_SCHEMA = {
    "name": "response_inspect",
    "description": (
        "Inspect HTTP responses from a .mitm capture file. "
        "Without endpoint filter, returns a summary of ALL flows. "
        "With endpoint filter (regex on URL), returns full request/response detail for matching flows."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "mitm_file": {"type": "string", "description": "Path to .mitm capture file"},
            "endpoint_filter": {
                "type": "string",
                "description": "Regex to filter by URL (optional). If omitted, returns summary of all flows.",
            },
        },
        "required": ["mitm_file"],
        "additionalProperties": False,
    },
    "allowed_callers": ["code_execution_20250825"],
}


def handle_response_inspect(mitm_file: str, endpoint_filter: str = "") -> str:
    """If no filter: return flow summaries. If filter: return full detail for matching flows."""
    flows = _read_flows(mitm_file)
    if not endpoint_filter:
        summaries = [_flow_summary(i, f) for i, f in enumerate(flows)]
        return json.dumps(summaries, indent=2, default=str)

    pattern = re.compile(endpoint_filter)
    details = []
    for i, flow in enumerate(flows):
        if pattern.search(flow.request.pretty_url):
            detail = _flow_detail(flow)
            detail["index"] = i
            details.append(detail)
    return json.dumps(details, indent=2, default=str)


# ── Tool 2: jwt_decode ──────────────────────────────────────────────

JWT_DECODE_SCHEMA = {
    "name": "jwt_decode",
    "description": (
        "Find all flows with Bearer tokens in a .mitm capture and decode the JWT claims. "
        "Answers: who is the authenticated user, what's in the token payload?"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "mitm_file": {"type": "string", "description": "Path to .mitm capture file"},
            "token_header": {
                "type": "string",
                "description": "Header name containing the token (default: Authorization)",
            },
        },
        "required": ["mitm_file"],
        "additionalProperties": False,
    },
    "allowed_callers": ["code_execution_20250825"],
}


def handle_jwt_decode(mitm_file: str, token_header: str = "Authorization") -> str:
    """Find auth'd flows, extract Bearer token, base64-decode JWT payload, return claims."""
    flows = _read_flows(mitm_file)
    results = []
    seen_tokens = set()
    for i, flow in enumerate(flows):
        header_val = flow.request.headers.get(token_header, "")
        if not header_val:
            continue
        token = header_val.replace("Bearer ", "").strip()
        if not token or token in seen_tokens:
            continue
        seen_tokens.add(token)
        parts = token.split(".")
        entry = {
            "flow_index": i,
            "url": flow.request.pretty_url,
            "token_preview": token[:40] + "..." if len(token) > 40 else token,
        }
        if len(parts) >= 2:
            try:
                payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                entry["claims"] = payload
            except Exception:
                entry["claims"] = "(decode failed)"
        results.append(entry)
    if not results:
        return json.dumps({"message": f"No flows found with {token_header} header"})
    return json.dumps(results, indent=2, default=str)


# ── Tool 3: header_audit ────────────────────────────────────────────

HEADER_AUDIT_SCHEMA = {
    "name": "header_audit",
    "description": (
        "Audit security headers across all flows in a .mitm capture. "
        "Checks for missing security headers, permissive CORS, server info leaks. "
        "Answers: how mature is this org's security posture?"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "mitm_file": {"type": "string", "description": "Path to .mitm capture file"},
        },
        "required": ["mitm_file"],
        "additionalProperties": False,
    },
    "allowed_callers": ["code_execution_20250825"],
}

_SECURITY_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
]


def handle_header_audit(mitm_file: str) -> str:
    """Sweep all flows for security headers, CORS posture, server info leaks."""
    flows = _read_flows(mitm_file)
    missing_by_url: dict[str, list[str]] = {}
    cors_issues: list[dict] = []
    server_leaks: list[dict] = []

    for i, flow in enumerate(flows):
        resp = flow.response
        if not resp:
            continue
        url = flow.request.pretty_url
        resp_headers = {k.lower(): v for k, v in resp.headers.items()}

        # Missing security headers
        missing = [h for h in _SECURITY_HEADERS if h.lower() not in resp_headers]
        if missing:
            missing_by_url[url] = missing

        # CORS check
        acao = resp_headers.get("access-control-allow-origin", "")
        if acao == "*":
            cors_issues.append({"flow_index": i, "url": url, "issue": "CORS allows all origins (*)."})
        acac = resp_headers.get("access-control-allow-credentials", "")
        if acac.lower() == "true" and acao == "*":
            cors_issues.append({"flow_index": i, "url": url, "issue": "CORS allows credentials with wildcard origin."})

        # Server info leaks
        for header in ("server", "x-powered-by", "x-aspnet-version"):
            val = resp_headers.get(header, "")
            if val:
                server_leaks.append({"flow_index": i, "url": url, "header": header, "value": val})

    report = {
        "total_flows": len(flows),
        "missing_security_headers": missing_by_url,
        "cors_issues": cors_issues,
        "server_info_leaks": server_leaks,
    }
    return json.dumps(report, indent=2, default=str)


# ── Tool 4: response_diff ───────────────────────────────────────────

RESPONSE_DIFF_SCHEMA = {
    "name": "response_diff",
    "description": (
        "Diff responses between two flows by index. "
        "Useful for comparing auth'd vs unauth'd, or same endpoint with different user contexts. "
        "Answers: where does auth state actually change behavior?"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "mitm_file": {"type": "string", "description": "Path to .mitm capture file"},
            "flow_index_a": {"type": "integer", "description": "Index of first flow to compare"},
            "flow_index_b": {"type": "integer", "description": "Index of second flow to compare"},
        },
        "required": ["mitm_file", "flow_index_a", "flow_index_b"],
        "additionalProperties": False,
    },
    "allowed_callers": ["code_execution_20250825"],
}


def handle_response_diff(mitm_file: str, flow_index_a: int, flow_index_b: int) -> str:
    """Structural diff of two flows' responses (status, headers, body)."""
    flows = _read_flows(mitm_file)
    if flow_index_a >= len(flows) or flow_index_b >= len(flows):
        return json.dumps({"error": f"Flow index out of range (total: {len(flows)})"})

    a = _flow_detail(flows[flow_index_a])
    b = _flow_detail(flows[flow_index_b])

    diff = {
        "flow_a": {"index": flow_index_a, "url": a["request"]["url"]},
        "flow_b": {"index": flow_index_b, "url": b["request"]["url"]},
        "status_diff": {"a": a["response"]["status"], "b": b["response"]["status"]},
    }

    # Header diff
    headers_a = set(a["response"]["headers"].keys())
    headers_b = set(b["response"]["headers"].keys())
    diff["headers_only_in_a"] = list(headers_a - headers_b)
    diff["headers_only_in_b"] = list(headers_b - headers_a)
    diff["header_value_diffs"] = {}
    for h in headers_a & headers_b:
        va = a["response"]["headers"][h]
        vb = b["response"]["headers"][h]
        if va != vb:
            diff["header_value_diffs"][h] = {"a": va, "b": vb}

    # Body diff
    body_a = json.dumps(a["response"]["body"], sort_keys=True, default=str) if a["response"]["body"] else ""
    body_b = json.dumps(b["response"]["body"], sort_keys=True, default=str) if b["response"]["body"] else ""
    diff["body_identical"] = body_a == body_b
    if not diff["body_identical"]:
        diff["body_a_preview"] = body_a[:2000]
        diff["body_b_preview"] = body_b[:2000]

    return json.dumps(diff, indent=2, default=str)


# ── Exports ──────────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    RESPONSE_INSPECT_SCHEMA,
    JWT_DECODE_SCHEMA,
    HEADER_AUDIT_SCHEMA,
    RESPONSE_DIFF_SCHEMA,
]

TOOL_HANDLERS = {
    "response_inspect": handle_response_inspect,
    "jwt_decode": handle_jwt_decode,
    "header_audit": handle_header_audit,
    "response_diff": handle_response_diff,
}
