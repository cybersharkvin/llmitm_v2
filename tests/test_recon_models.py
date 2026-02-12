"""Test recon models for validation and serialization."""

import json

import pytest

from llmitm_v2.models.recon import (
    AttackOpportunity,
    DiscoveredEndpoint,
    ReconCriticFeedback,
    ReconReport,
)


@pytest.fixture
def sample_endpoint():
    return DiscoveredEndpoint(
        method="GET", path="/api/Users/1", status_code=200,
        response_summary="Returns user object with email and role",
        auth_required=False, parameters=["id"],
        tool_context="http_request GET /api/Users/1",
    )


@pytest.fixture
def sample_opportunity():
    return AttackOpportunity(
        endpoint="/api/Users/1", vulnerability_type="IDOR",
        evidence="GET /api/Users/1 returns full user object without auth",
        suggested_attack="Auth as user B, access user A via /api/Users/{A_id}",
        confidence=0.85, tool_context="http_request GET /api/Users/1",
    )


@pytest.fixture
def sample_report(sample_endpoint, sample_opportunity):
    return ReconReport(
        tech_stack="Express.js", auth_model="JWT Bearer",
        endpoint_pattern="/api/*", security_signals=["CORS permissive", "no CSP"],
        target_url="http://localhost:3000",
        endpoints_discovered=[sample_endpoint],
        attack_opportunities=[sample_opportunity],
    )


class TestDiscoveredEndpoint:
    def test_creation(self, sample_endpoint):
        assert sample_endpoint.method == "GET" and sample_endpoint.status_code == 200

    def test_serialization(self, sample_endpoint):
        data = json.loads(sample_endpoint.model_dump_json())
        assert DiscoveredEndpoint(**data) == sample_endpoint


class TestAttackOpportunity:
    def test_creation(self, sample_opportunity):
        assert sample_opportunity.vulnerability_type == "IDOR" and sample_opportunity.confidence == 0.85

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            AttackOpportunity(
                endpoint="/x", vulnerability_type="x", evidence="x",
                suggested_attack="x", confidence=1.5, tool_context="x",
            )

    def test_serialization(self, sample_opportunity):
        data = json.loads(sample_opportunity.model_dump_json())
        assert AttackOpportunity(**data) == sample_opportunity


class TestReconReport:
    def test_creation(self, sample_report):
        assert sample_report.tech_stack == "Express.js" and len(sample_report.endpoints_discovered) == 1

    def test_to_fingerprint(self, sample_report):
        fp = sample_report.to_fingerprint()
        assert fp.hash is not None and fp.tech_stack == "Express.js" and fp.endpoint_pattern == "/api/*"

    def test_to_fingerprint_deterministic(self, sample_report):
        fp1 = sample_report.to_fingerprint()
        fp2 = sample_report.to_fingerprint()
        assert fp1.hash == fp2.hash

    def test_traffic_log_default_empty(self, sample_report):
        assert sample_report.traffic_log == ""

    def test_serialization(self, sample_report):
        data = json.loads(sample_report.model_dump_json())
        assert ReconReport(**data) == sample_report


class TestReconCriticFeedback:
    def test_passed(self):
        fb = ReconCriticFeedback(passed=True, feedback="Looks good")
        assert fb.passed is True and fb.false_positives == []

    def test_rejected_with_details(self):
        fb = ReconCriticFeedback(passed=False, feedback="Bad evidence", false_positives=["SQLi"], missing_coverage=["GraphQL"])
        assert not fb.passed and len(fb.false_positives) == 1

    def test_serialization(self):
        fb = ReconCriticFeedback(passed=True, feedback="OK")
        assert ReconCriticFeedback(**json.loads(fb.model_dump_json())) == fb
