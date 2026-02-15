"""Attack plan models for the Recon Agent -> Attack Critic pipeline.

The Recon Agent produces an AttackPlan (list of opportunities with prescribed exploit tools).
The Attack Critic receives the same JSON and produces a refined AttackPlan.
Both are constrained by the same schema — same enum of recon tools and exploit tools.
"""

from typing import List, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


# Recon tool enum — agent can only cite tools it actually called
ReconTool = Literal["response_inspect", "jwt_decode", "header_audit", "response_diff"]

# Exploit tool enum — agent can only prescribe from this fixed set
ExploitTool = Literal["idor_walk", "auth_strip", "token_swap", "namespace_probe", "role_tamper"]


class AttackOpportunity(BaseModel):
    """Single attack opportunity with recon evidence and prescribed exploit."""

    opportunity: str = Field(description="Short name for this opportunity (e.g., 'IDOR on User Profiles')")
    recon_tool_used: ReconTool = Field(description="Which recon tool surfaced the evidence")
    observation: str = Field(description="What the traffic showed — specific data from tool output")
    suspected_gap: str = Field(description="Business intent -> developer assumption -> code behavior — where did fidelity degrade?")
    recommended_exploit: ExploitTool = Field(description="Which exploit tool to run against this target")
    exploit_target: str = Field(description="Concrete URL path with real IDs from traffic (e.g., '/api/Users/1'). Must be a path, not a full URL. Never use templates like {id}.")
    exploit_reasoning: str = Field(description="Why this exploit tool + target combination tests the suspected gap")

    @field_validator("exploit_target")
    @classmethod
    def must_be_concrete_path(cls, v: str) -> str:
        """Ensure exploit_target is a concrete path, not a template or full URL."""
        if "{" in v:
            v = v.replace("{id}", "1").replace("{", "").replace("}", "")
        parsed = urlparse(v)
        if parsed.scheme:
            v = parsed.path
        return v


class AttackPlan(BaseModel):
    """Complete output of the Recon Agent. List of ready-to-execute exploit prescriptions."""

    attack_plan: List[AttackOpportunity] = Field(description="Prioritized list of attack opportunities")
