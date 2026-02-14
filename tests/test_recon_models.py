"""Test attack plan models for validation and serialization."""

import json

import pytest

from llmitm_v2.models.recon import AttackOpportunity, AttackPlan


@pytest.fixture
def sample_opportunity():
    return AttackOpportunity(
        opportunity="IDOR on /api/Users/{id}",
        recon_tool_used="response_inspect",
        observation="GET /api/Users/1 returns full user object with email and role",
        suspected_gap="Business expects owner-only access; code returns data for any valid ID",
        recommended_exploit="idor_walk",
        exploit_target="/api/Users/1",
        exploit_reasoning="ID in URL + no ownership check = classic IDOR",
    )


@pytest.fixture
def sample_plan(sample_opportunity):
    return AttackPlan(attack_plan=[sample_opportunity])


class TestAttackOpportunity:
    def test_creation(self, sample_opportunity):
        assert sample_opportunity.recommended_exploit == "idor_walk" and sample_opportunity.recon_tool_used == "response_inspect"

    def test_invalid_recon_tool(self):
        with pytest.raises(Exception):
            AttackOpportunity(
                opportunity="x", recon_tool_used="invalid_tool", observation="x",
                suspected_gap="x", recommended_exploit="idor_walk", exploit_target="/x", exploit_reasoning="x",
            )

    def test_invalid_exploit_tool(self):
        with pytest.raises(Exception):
            AttackOpportunity(
                opportunity="x", recon_tool_used="response_inspect", observation="x",
                suspected_gap="x", recommended_exploit="invalid_exploit", exploit_target="/x", exploit_reasoning="x",
            )

    def test_serialization(self, sample_opportunity):
        data = json.loads(sample_opportunity.model_dump_json())
        assert AttackOpportunity(**data) == sample_opportunity


class TestAttackPlan:
    def test_creation(self, sample_plan):
        assert len(sample_plan.attack_plan) == 1 and sample_plan.attack_plan[0].recommended_exploit == "idor_walk"

    def test_empty_plan(self):
        plan = AttackPlan(attack_plan=[])
        assert len(plan.attack_plan) == 0

    def test_serialization(self, sample_plan):
        data = json.loads(sample_plan.model_dump_json())
        assert AttackPlan(**data) == sample_plan

    def test_multiple_opportunities(self, sample_opportunity):
        opp2 = sample_opportunity.model_copy(update={"recommended_exploit": "auth_strip", "opportunity": "Auth strip on /api/Products"})
        plan = AttackPlan(attack_plan=[sample_opportunity, opp2])
        assert len(plan.attack_plan) == 2
