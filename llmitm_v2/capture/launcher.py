"""Capture launcher: fingerprinting for warm-start fast path.

Provides:
- quick_fingerprint(): Live HTTP probes for fingerprint extraction
- fingerprint_from_mitm(): Offline fingerprint from .mitm capture file
"""

import logging
from typing import Optional

import httpx
from mitmproxy.io import FlowReader

from llmitm_v2.fingerprinter import Fingerprinter
from llmitm_v2.models.fingerprint import Fingerprint

logger = logging.getLogger(__name__)


def quick_fingerprint(target_url: str) -> Optional[Fingerprint]:
    """Send a few deterministic requests directly to target, extract fingerprint from headers.

    Uses existing Fingerprinter logic. Returns Fingerprint if enough data, None if not.
    This is the warm-start fast path — zero LLM cost, no proxy needed.
    """
    client = httpx.Client(timeout=10, verify=False)

    traffic_lines = []
    for path in ["/", "/api/", "/rest/"]:
        try:
            url = target_url.rstrip("/") + path
            resp = client.get(url)
            traffic_lines.append(f">>> GET {path} HTTP/1.1")
            traffic_lines.append(f"Host: {target_url.split('://')[-1]}")
            traffic_lines.append("")
            traffic_lines.append(f"<<< HTTP/1.1 {resp.status_code}")
            for k, v in resp.headers.items():
                traffic_lines.append(f"{k}: {v}")
            body_preview = resp.text[:500]
            if body_preview:
                traffic_lines.append("")
                traffic_lines.append(body_preview)
            traffic_lines.append("")
        except Exception:
            continue

    if not traffic_lines:
        return None

    traffic_log = "\n".join(traffic_lines)
    try:
        fp = Fingerprinter().fingerprint(traffic_log)
        fp.ensure_hash()
        return fp
    except Exception:
        return None


def fingerprint_from_mitm(mitm_path: str) -> Optional[Fingerprint]:
    """Extract fingerprint from a .mitm capture file using FlowReader.

    Reads .mitm binary directly, builds >>> / <<< formatted traffic for Fingerprinter.
    No live target or subprocess needed.
    """
    try:
        traffic_lines: list[str] = []
        with open(mitm_path, "rb") as f:
            for flow in FlowReader(f).stream():
                req = flow.request
                traffic_lines.append(f">>> {req.method} {req.path} HTTP/1.1")
                for k, v in req.headers.items():
                    traffic_lines.append(f"{k}: {v}")
                if req.text:
                    traffic_lines.append("")
                    traffic_lines.append(req.text[:500])
                traffic_lines.append("")

                resp = flow.response
                if resp:
                    traffic_lines.append(f"<<< HTTP/1.1 {resp.status_code}")
                    for k, v in resp.headers.items():
                        traffic_lines.append(f"{k}: {v}")
                    body = resp.text[:500] if resp.text else ""
                    if body:
                        traffic_lines.append("")
                        traffic_lines.append(body)
                    traffic_lines.append("")

        if not traffic_lines:
            return None

        fp = Fingerprinter().fingerprint("\n".join(traffic_lines))
        fp.ensure_hash()
        return fp
    except Exception:
        logger.warning("Failed to fingerprint from %s", mitm_path, exc_info=True)
        return None
