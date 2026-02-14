"""Attack plan models for the Recon Agent -> Attack Critic pipeline.

The Recon Agent produces an AttackPlan (list of opportunities with prescribed exploit tools).
The Attack Critic receives the same JSON and produces a refined AttackPlan.
Both are constrained by the same schema — same enum of recon tools and exploit tools.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


# Recon tool enum — agent can only cite tools it actually called
ReconTool = Literal["response_inspect", "jwt_decode", "header_audit", "response_diff"]

# Exploit tool enum — agent can only prescribe from this fixed set
ExploitTool = Literal["idor_walk", "auth_strip", "token_swap", "namespace_probe", "role_tamper"]


class AttackOpportunity(BaseModel):
    """Single attack opportunity with recon evidence and prescribed exploit."""

    opportunity: str = Field(description="Short name for this opportunity (e.g., 'IDOR on /api/Users/{id}')")
    recon_tool_used: ReconTool = Field(description="Which recon tool surfaced the evidence")
    observation: str = Field(description="What the traffic showed — specific data from tool output")
    suspected_gap: str = Field(description="Business intent -> developer assumption -> code behavior — where did fidelity degrade?")
    recommended_exploit: ExploitTool = Field(description="Which exploit tool to run against this target")
    exploit_target: str = Field(description="Specific endpoint/resource to target (e.g., '/api/Users/{id}')")
    exploit_reasoning: str = Field(description="Why this exploit tool + target combination tests the suspected gap")


class AttackPlan(BaseModel):
    """Complete output of the Recon Agent. List of ready-to-execute exploit prescriptions."""

    attack_plan: List[AttackOpportunity] = Field(description="Prioritized list of attack opportunities")
