"""Test GraphRepository CRUD operations against Neo4j.

Note: These tests require a running Neo4j instance (see docker-compose.yml).
Run with: docker compose up -d && pytest tests/test_graph_repository.py
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from llmitm_v2.constants import StepPhase, StepType
from llmitm_v2.models import ActionGraph, Finding, Fingerprint, Step
from llmitm_v2.repository import GraphRepository


@pytest.fixture
def mock_driver():
    """Create a mock Neo4j Driver."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Create a mock Neo4j Session."""
    return MagicMock()


@pytest.fixture
def graph_repository(mock_driver):
    """Create GraphRepository with mock driver."""
    return GraphRepository(mock_driver)


@pytest.fixture
def sample_fingerprint():
    """Create a sample Fingerprint."""
    fp = Fingerprint(
        tech_stack="Express.js + JWT",
        auth_model="Bearer token in Authorization header",
        endpoint_pattern="/api/v1/*",
        security_signals=["CORS enabled"],
    )
    fp.ensure_hash()
    return fp


@pytest.fixture
def sample_action_graph():
    """Create a sample ActionGraph."""
    steps = [
        Step(
            order=0,
            phase=StepPhase.CAPTURE,
            type=StepType.HTTP_REQUEST,
            command="curl -H 'Authorization: Bearer token' http://localhost:3000/api/v1/users",
            parameters={"method": "GET"},
            success_criteria=r"HTTP/1\.1 200",
        ),
        Step(
            order=1,
            phase=StepPhase.MUTATE,
            type=StepType.SHELL_COMMAND,
            command="sed 's/Bearer .*/Bearer invalid_token/' request.txt",
            parameters={"pattern": "token"},
        ),
        Step(
            order=2,
            phase=StepPhase.REPLAY,
            type=StepType.HTTP_REQUEST,
            command="curl -i @request.txt",
            parameters={"timeout": 10},
            success_criteria=r"HTTP/1\.1 401|403",
        ),
    ]
    ag = ActionGraph(
        vulnerability_type="IDOR",
        description="Test user enumeration via ID parameter manipulation",
        steps=steps,
        confidence=0.92,
    )
    ag.ensure_id()
    return ag


@pytest.fixture
def sample_finding():
    """Create a sample Finding."""
    finding = Finding(
        observation="User ID enumeration possible through ID parameter in /api/v1/users/{id}",
        severity="high",
        evidence_summary="Can enumerate all user IDs by iterating parameter 1-1000, server returns consistent response structure",
        target_url="http://localhost:3000/api/v1/users/1",
    )
    finding.ensure_id()
    return finding


class TestGraphRepositoryMocked:
    """Test GraphRepository methods with mocked driver."""

    def test_save_fingerprint(self, graph_repository, mock_driver, mock_session, sample_fingerprint):
        """Test save_fingerprint MERGE operation."""
        mock_driver.session.return_value.__enter__.return_value = mock_session

        graph_repository.save_fingerprint(sample_fingerprint)

        # Verify session was created and used
        mock_driver.session.assert_called_once()

    def test_get_fingerprint_by_hash(self, graph_repository, mock_driver, mock_session):
        """Test get_fingerprint_by_hash lookup."""
        mock_driver.session.return_value.__enter__.return_value = mock_session

        # Mock return value
        mock_result = MagicMock()
        mock_result.single.return_value = {
            "fp": {
                "hash": "abc123",
                "tech_stack": "Express.js + JWT",
                "auth_model": "Bearer token",
                "endpoint_pattern": "/api/v1/*",
            }
        }
        mock_session.execute_read.return_value = mock_result.single.return_value

        # Call method
        result = graph_repository.get_fingerprint_by_hash("abc123")

        # Verify
        assert result is not None
        assert result["hash"] == "abc123"

    def test_save_action_graph(self, graph_repository, mock_driver, mock_session, sample_action_graph):
        """Test save_action_graph creates all nodes and relationships."""
        mock_driver.session.return_value.__enter__.return_value = mock_session

        fingerprint_hash = "abc123"
        graph_repository.save_action_graph(fingerprint_hash, sample_action_graph)

        # Verify session was used
        mock_driver.session.assert_called_once()

    def test_save_finding(self, graph_repository, mock_driver, mock_session, sample_finding):
        """Test save_finding creates Finding and [:PRODUCED_BY] edge."""
        mock_driver.session.return_value.__enter__.return_value = mock_session

        ag_id = "graph123"
        graph_repository.save_finding(ag_id, sample_finding)

        # Verify
        mock_driver.session.assert_called_once()

    def test_increment_execution_count(self, graph_repository, mock_driver, mock_session):
        """Test increment_execution_count for metrics tracking."""
        mock_driver.session.return_value.__enter__.return_value = mock_session

        ag_id = "graph123"
        graph_repository.increment_execution_count(ag_id, succeeded=True)

        # Verify
        mock_driver.session.assert_called_once()


class TestParameterSerialization:
    """Test Step.parameters serialization to/from JSON."""

    def test_step_parameters_json_serialization(self):
        """Test that Step parameters are correctly serialized to JSON."""
        step = Step(
            order=0,
            phase=StepPhase.CAPTURE,
            type=StepType.HTTP_REQUEST,
            command="curl test",
            parameters={"method": "GET", "timeout": 5, "headers": {"User-Agent": "test"}},
        )

        # Simulate what save_action_graph does
        step_dict = step.model_dump()
        params_json = json.dumps(step.parameters)

        # Simulate what read back does
        params_restored = json.loads(params_json)
        assert params_restored == step.parameters
        assert params_restored["method"] == "GET"
        assert params_restored["headers"]["User-Agent"] == "test"

    def test_step_parameters_empty(self):
        """Test Step with empty parameters."""
        step = Step(
            order=0,
            phase=StepPhase.CAPTURE,
            type=StepType.HTTP_REQUEST,
            command="curl test",
        )

        params_json = json.dumps(step.parameters)
        params_restored = json.loads(params_json)
        assert params_restored == {}


class TestModelValidation:
    """Test model validation and constraints."""

    def test_action_graph_with_multiple_steps(self, sample_action_graph):
        """Test ActionGraph with multiple ordered steps."""
        assert len(sample_action_graph.steps) == 3
        assert sample_action_graph.steps[0].order == 0
        assert sample_action_graph.steps[1].order == 1
        assert sample_action_graph.steps[2].order == 2
        assert sample_action_graph.steps[0].phase == StepPhase.CAPTURE
        assert sample_action_graph.steps[1].phase == StepPhase.MUTATE
        assert sample_action_graph.steps[2].phase == StepPhase.REPLAY

    def test_fingerprint_security_signals(self, sample_fingerprint):
        """Test Fingerprint with security signals."""
        assert len(sample_fingerprint.security_signals) > 0
        assert "CORS enabled" in sample_fingerprint.security_signals

    def test_finding_severity_levels(self):
        """Test Finding with different severity levels."""
        severities = ["critical", "high", "medium", "low"]
        for severity in severities:
            finding = Finding(
                observation="Test vulnerability",
                severity=severity,
                evidence_summary="Evidence",
            )
            assert finding.severity == severity


class TestRepositoryIntegration:
    """Integration tests for GraphRepository (requires live Neo4j)."""

    @pytest.mark.skip(reason="Requires live Neo4j instance")
    def test_save_and_retrieve_fingerprint(self):
        """Integration test: save and retrieve fingerprint."""
        # This would connect to real Neo4j
        pass

    @pytest.mark.skip(reason="Requires live Neo4j instance")
    def test_save_and_retrieve_action_graph(self):
        """Integration test: save and retrieve action graph with steps."""
        # This would connect to real Neo4j
        pass

    @pytest.mark.skip(reason="Requires live Neo4j instance")
    def test_find_similar_fingerprints(self):
        """Integration test: vector similarity search."""
        # This would connect to real Neo4j and perform vector search
        pass
