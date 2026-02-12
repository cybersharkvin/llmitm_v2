"""Recon models for LLM-driven active reconnaissance."""

from typing import List

from pydantic import BaseModel, Field

from llmitm_v2.models.fingerprint import Fingerprint


class DiscoveredEndpoint(BaseModel):
    """Single HTTP endpoint discovered during active recon."""

    method: str = Field(description="HTTP method used (GET, POST, PUT, DELETE, etc.)")
    path: str = Field(description="URL path relative to target root (e.g., /api/Users, /rest/user/login)")
    status_code: int = Field(description="HTTP response status code received")
    response_summary: str = Field(description="One-line description of what the endpoint returns and its purpose")
    auth_required: bool = Field(description="True if endpoint returned 401/403 without auth, or required a token")
    parameters: List[str] = Field(default_factory=list, description="Discovered query params, body fields, or path params")
    tool_context: str = Field(description="Which tool call discovered this (e.g., 'http_request GET /api/Users') for audit trail")


class AttackOpportunity(BaseModel):
    """Suspected vulnerability identified from recon observations."""

    endpoint: str = Field(description="Target endpoint path where the vulnerability was observed")
    vulnerability_type: str = Field(description="Vulnerability class: IDOR, auth_bypass, privesc, injection, info_disclosure, etc.")
    evidence: str = Field(description="Specific observation that suggests this vulnerability (e.g., 'GET /api/Users/1 returns full user object without auth check')")
    suggested_attack: str = Field(description="Brief attack approach to confirm the vulnerability (e.g., 'Authenticate as user B, access user A profile via /api/Users/{A_id}')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0.0-1.0 based on strength of evidence")
    tool_context: str = Field(description="Which tool calls produced the evidence for this opportunity")


class ReconReport(BaseModel):
    """Complete structured output of the recon agent. Replaces both Fingerprint and traffic_log."""

    # Fingerprint fields
    tech_stack: str = Field(description="Identified technology stack (e.g., 'Express.js', 'Django + PostgreSQL'). Determined from response headers, error messages, and behavior.")
    auth_model: str = Field(description="Authentication mechanism identified (e.g., 'JWT Bearer', 'Cookie-based session', 'API key in header'). Determined from auth endpoints and header patterns.")
    endpoint_pattern: str = Field(description="Primary API pattern (e.g., '/api/*', '/rest/*', '/graphql'). Most common path prefix observed.")
    security_signals: List[str] = Field(default_factory=list, description="Security indicators observed (e.g., 'CORS permissive', 'no CSP', 'verbose error messages', 'missing rate limiting')")

    # Discovery results
    target_url: str = Field(description="Base URL of the target application that was explored")
    endpoints_discovered: List[DiscoveredEndpoint] = Field(description="All endpoints discovered during recon, in order of discovery")
    attack_opportunities: List[AttackOpportunity] = Field(description="Suspected vulnerabilities ranked by confidence, each with evidence and tool context")

    # Raw traffic log — assembled by launcher from mitmproxy addon output, NOT by LLM
    traffic_log: str = Field(default="", description="Raw HTTP traffic in >>> / <<< format. Populated by the capture system, not the LLM.")

    def to_fingerprint(self) -> Fingerprint:
        """Convert recon results to a Fingerprint for Neo4j storage and warm-start matching."""
        fp = Fingerprint(
            tech_stack=self.tech_stack,
            auth_model=self.auth_model,
            endpoint_pattern=self.endpoint_pattern,
            security_signals=self.security_signals,
        )
        fp.ensure_hash()
        return fp


