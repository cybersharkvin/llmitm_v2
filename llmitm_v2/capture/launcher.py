"""Capture launcher: quick fingerprint for warm-start fast path.

The recon agent loop is now handled by the Orchestrator._compile() method.
This module only provides quick_fingerprint() for the warm-start fast path.
"""

import logging
from typing import Optional

import httpx

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
