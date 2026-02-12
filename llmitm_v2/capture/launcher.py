"""Capture launcher: manages mitmproxy subprocess and recon agent lifecycle.

Two entry points:
- quick_fingerprint(): Deterministic fast path — zero LLM cost
- run_recon(): Full LLM-driven recon — only called when quick_fingerprint misses
"""

import json
import logging
import socket
import time
from pathlib import Path
from typing import Optional

import httpx

from llmitm_v2.config import Settings
from llmitm_v2.fingerprinter import Fingerprinter
from llmitm_v2.models.fingerprint import Fingerprint
from llmitm_v2.models.recon import ReconCriticFeedback, ReconReport
from llmitm_v2.orchestrator.agents import create_recon_agent, create_recon_critic_agent
from llmitm_v2.orchestrator.context import assemble_recon_context

logger = logging.getLogger(__name__)


def _wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 10.0) -> bool:
    """Wait until a TCP port is accepting connections."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def _format_traffic_log(flows: list[dict]) -> str:
    """Convert captured flow dicts into >>> / <<< text format."""
    lines = []
    for flow in flows:
        # Request
        method = flow.get("request_method", "GET")
        path = flow.get("request_path", "/")
        lines.append(f">>> {method} {path} HTTP/1.1")
        for k, v in flow.get("request_headers", {}).items():
            lines.append(f"{k}: {v}")
        body = flow.get("request_body", "")
        if body:
            lines.append("")
            lines.append(body)
        lines.append("")

        # Response
        status = flow.get("response_status_code", 200)
        lines.append(f"<<< HTTP/1.1 {status}")
        for k, v in flow.get("response_headers", {}).items():
            lines.append(f"{k}: {v}")
        resp_body = flow.get("response_body", "")
        if resp_body:
            lines.append("")
            lines.append(resp_body[:2000])
        lines.append("")

    return "\n".join(lines)


def quick_fingerprint(target_url: str) -> Optional[Fingerprint]:
    """Send a few deterministic requests directly to target, extract fingerprint from headers.

    Uses existing Fingerprinter logic. Returns Fingerprint if enough data, None if not.
    This is the warm-start fast path — zero LLM cost, no proxy needed.
    """
    client = httpx.Client(timeout=10, verify=False)

    # Collect minimal traffic for fingerprinting
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


def run_recon(settings: Settings) -> ReconReport:
    """Full LLM-driven recon. Uses Docker mitmproxy running on mitm_port.

    Docker compose starts mitmproxy with addon.py mounted, capturing flows to /capture/flows.json.
    This function:
    1. Verify Docker mitmproxy is running on mitm_port via _wait_for_port()
    2. Delete stale flows.json from previous run
    3. Create recon agent + recon critic
    4. Recon/critic loop (max recon_max_iterations) — agent makes HTTP requests through proxy
    5. Addon captures flows to /capture/flows.json (via Docker volume mount)
    6. Read flows file and format into traffic_log
    7. Return validated ReconReport
    """
    proxy_port = settings.mitm_port
    target_url = settings.target_url
    proxy_url = f"http://127.0.0.1:{proxy_port}"
    flows_file_path = Path(settings.flows_file)

    # Delete stale flows file from previous run
    if flows_file_path.exists():
        flows_file_path.unlink()
        logger.info("Deleted stale flows file: %s", flows_file_path)

    # Verify Docker mitmproxy is running
    if not _wait_for_port(proxy_port):
        raise RuntimeError(
            f"Docker mitmproxy not running on port {proxy_port}. "
            f"Start with: docker compose up -d"
        )
    logger.info("Docker mitmproxy ready on port %d", proxy_port)

    # Create agents
    recon_agent = create_recon_agent(
        proxy_url=proxy_url,
        model_id=settings.recon_model_id,
        api_key=settings.anthropic_api_key,
    )
    recon_critic = create_recon_critic_agent(
        model_id=settings.recon_model_id,
        api_key=settings.anthropic_api_key,
    )

    # Build initial prompt
    prompt = assemble_recon_context(target_url)
    report: Optional[ReconReport] = None

    # Recon/critic loop
    for iteration in range(1, settings.recon_max_iterations + 1):
        logger.info("Recon iteration %d/%d", iteration, settings.recon_max_iterations)

        # Recon agent explores via Docker proxy
        recon_result = recon_agent(prompt, structured_output_model=ReconReport)
        report = recon_result.structured_output

        # Critic validates
        critic_result = recon_critic(
            report.model_dump_json(),
            structured_output_model=ReconCriticFeedback,
        )
        feedback: ReconCriticFeedback = critic_result.structured_output

        if feedback.passed:
            logger.info("Recon critic passed on iteration %d", iteration)
            break

        # Append feedback and retry
        logger.info("Recon critic rejected: %s", feedback.feedback)
        prompt += f"\n\nCRITIC FEEDBACK (iteration {iteration}):\n{feedback.feedback}"
        if feedback.false_positives:
            prompt += f"\nFalse positives flagged: {', '.join(feedback.false_positives)}"
        if feedback.missing_coverage:
            prompt += f"\nMissing coverage: {', '.join(feedback.missing_coverage)}"

    if report is None:
        raise RuntimeError("Recon agent produced no report")

    # Read captured flows from mounted volume
    flows = []
    if flows_file_path.exists():
        try:
            flows = json.loads(flows_file_path.read_text())
            logger.info("Read %d flows from %s", len(flows), flows_file_path)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Could not read flows file %s: %s", flows_file_path, e)
    else:
        logger.warning("Flows file not created at %s (addon may not be running in Docker)", flows_file_path)

    # Format traffic log and attach to report
    report.traffic_log = _format_traffic_log(flows)

    logger.info(
        "Recon complete: %d endpoints, %d opportunities, %d captured flows",
        len(report.endpoints_discovered),
        len(report.attack_opportunities),
        len(flows),
    )
    return report
