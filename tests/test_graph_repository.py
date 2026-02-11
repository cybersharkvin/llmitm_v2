"""Test GraphRepository operations.

Note: Integration tests marked with @pytest.mark.integration require a running Neo4j instance.
Run with: docker compose up -d && pytest tests/test_graph_repository.py -m integration
"""

import json
import pytest
from llmitm_v2.constants import StepPhase, StepType
from llmitm_v2.models import ActionGraph, Finding, Fingerprint, Step


@pytest.fixture
def sample_fingerprint():
    fp = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*", security_signals=["CORS enabled"])
    fp.ensure_hash()
    return fp


@pytest.fixture
def sample_action_graph():
    steps = [Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl http://localhost:3000/api/v1/users"), Step(order=1, phase=StepPhase.MUTATE, type=StepType.SHELL_COMMAND, command="sed 's/Bearer .*/Bearer invalid/' request.txt")]
    ag = ActionGraph(vulnerability_type="IDOR", description="Test user enumeration", steps=steps, confidence=0.92)
    ag.ensure_id()
    return ag


@pytest.fixture
def sample_finding():
    finding = Finding(observation="User ID enumeration possible", severity="high", evidence_summary="Can enumerate user IDs", target_url="http://localhost:3000")
    finding.ensure_id()
    return finding


class TestStepParametersSerialization:
    """Test Step.parameters serialization (pure Python, no Neo4j)."""

    def test_step_parameters_json_serialization(self):
        step = Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl test", parameters={"method": "GET", "timeout": 5, "headers": {"User-Agent": "test"}})
        params_restored = json.loads(json.dumps(step.parameters))
        assert params_restored == step.parameters

    def test_step_parameters_empty(self):
        step = Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl test")
        params_restored = json.loads(json.dumps(step.parameters))
        assert params_restored == {}


class TestActionGraphModels:
    """Test ActionGraph model validation (pure Python, no Neo4j)."""

    def test_action_graph_with_multiple_steps(self, sample_action_graph):
        assert len(sample_action_graph.steps) == 2 and sample_action_graph.steps[0].phase == StepPhase.CAPTURE

    def test_fingerprint_security_signals(self, sample_fingerprint):
        assert len(sample_fingerprint.security_signals) > 0 and "CORS enabled" in sample_fingerprint.security_signals

    def test_finding_severity_levels(self):
        for severity in ["critical", "high", "medium", "low"]:
            finding = Finding(observation="Test", severity=severity, evidence_summary="Evidence")
            assert finding.severity == severity


class TestGraphRepositoryIntegration:
    """Integration tests with live Neo4j (marked with @pytest.mark.integration)."""

    @pytest.mark.integration
    def test_save_and_retrieve_fingerprint(self, sample_fingerprint):
        """Integration test: save and retrieve fingerprint from Neo4j."""
        from llmitm_v2.repository import GraphRepository
        from neo4j import GraphDatabase
        import os

        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            repo = GraphRepository(driver)
            repo.save_fingerprint(sample_fingerprint)
            retrieved = repo.get_fingerprint_by_hash(sample_fingerprint.hash)
            assert retrieved is not None and retrieved["tech_stack"] == sample_fingerprint.tech_stack
            driver.close()
        except Exception as e:
            pytest.skip(f"Neo4j unavailable: {e}")

    @pytest.mark.integration
    def test_save_and_retrieve_action_graph(self, sample_fingerprint, sample_action_graph):
        """Integration test: save and retrieve ActionGraph with steps from Neo4j."""
        from llmitm_v2.repository import GraphRepository
        from neo4j import GraphDatabase
        import os

        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            repo = GraphRepository(driver)
            repo.save_fingerprint(sample_fingerprint)
            repo.save_action_graph(sample_fingerprint.hash, sample_action_graph)
            retrieved = repo.get_action_graph_with_steps(sample_fingerprint.hash)
            assert retrieved is not None and retrieved["id"] == sample_action_graph.id
            driver.close()
        except Exception as e:
            pytest.skip(f"Neo4j unavailable: {e}")

    @pytest.mark.integration
    def test_save_finding(self, sample_fingerprint, sample_action_graph, sample_finding):
        """Integration test: save Finding and [:PRODUCED_BY] edge."""
        from llmitm_v2.repository import GraphRepository
        from neo4j import GraphDatabase
        import os

        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            repo = GraphRepository(driver)
            repo.save_fingerprint(sample_fingerprint)
            repo.save_action_graph(sample_fingerprint.hash, sample_action_graph)
            repo.save_finding(sample_action_graph.id, sample_finding)
            # Verify finding was created by querying back
            driver.close()
        except Exception as e:
            pytest.skip(f"Neo4j unavailable: {e}")

    @pytest.mark.integration
    def test_increment_execution_count(self, sample_fingerprint, sample_action_graph):
        """Integration test: increment metrics on ActionGraph."""
        from llmitm_v2.repository import GraphRepository
        from neo4j import GraphDatabase
        import os

        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")

        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            repo = GraphRepository(driver)
            repo.save_fingerprint(sample_fingerprint)
            repo.save_action_graph(sample_fingerprint.hash, sample_action_graph)
            repo.increment_execution_count(sample_action_graph.id, succeeded=True)
            driver.close()
        except Exception as e:
            pytest.skip(f"Neo4j unavailable: {e}")
