"""Tests for orchestration layer: agents, context, failure classification."""

import pytest

from llmitm_v2.constants import FailureType, StepPhase, StepType
from llmitm_v2.models import Fingerprint, Step
from llmitm_v2.orchestrator import (
    assemble_recon_context,
    assemble_repair_context,
    classify_failure,
    create_attack_critic,
    create_recon_agent,
)

try:
    from llmitm_v2.repository import GraphRepository
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False


class TestFailureClassification:
    """Tests for deterministic failure classification."""

    def test_classify_failure_timeout_is_recoverable(self):
        result = classify_failure("Connection timeout after 30s", 0)
        assert result == FailureType.TRANSIENT_RECOVERABLE

    def test_classify_failure_503_is_recoverable(self):
        result = classify_failure("Service Unavailable", 503)
        assert result == FailureType.TRANSIENT_RECOVERABLE

    def test_classify_failure_429_is_recoverable(self):
        result = classify_failure("Too Many Requests", 429)
        assert result == FailureType.TRANSIENT_RECOVERABLE

    def test_classify_failure_404_is_unrecoverable(self):
        result = classify_failure("Not Found", 404)
        assert result == FailureType.TRANSIENT_UNRECOVERABLE

    def test_classify_failure_401_is_unrecoverable(self):
        result = classify_failure("Unauthorized", 401)
        assert result == FailureType.TRANSIENT_UNRECOVERABLE

    def test_classify_failure_403_is_unrecoverable(self):
        result = classify_failure("Forbidden", 403)
        assert result == FailureType.TRANSIENT_UNRECOVERABLE

    def test_classify_failure_session_expired_is_unrecoverable(self):
        result = classify_failure("Session expired", 0)
        assert result == FailureType.TRANSIENT_UNRECOVERABLE

    def test_classify_failure_unknown_is_systemic(self):
        result = classify_failure("Unexpected error: AttributeError", 0)
        assert result == FailureType.SYSTEMIC

    def test_classify_failure_reset_is_recoverable(self):
        result = classify_failure("Connection reset by peer", 0)
        assert result == FailureType.TRANSIENT_RECOVERABLE


class TestContextAssembly:
    """Tests for context assembly functions."""

    def test_assemble_recon_context_file_mode(self):
        ctx = assemble_recon_context(mitm_file="demo/juice_shop.mitm")
        assert "juice_shop.mitm" in ctx
        assert "TASK:" in ctx

    def test_assemble_recon_context_live_mode(self):
        ctx = assemble_recon_context(proxy_url="http://127.0.0.1:8080")
        assert "127.0.0.1:8080" in ctx
        assert "TASK:" in ctx

    def test_assemble_recon_context_error_when_no_args(self):
        ctx = assemble_recon_context()
        assert "ERROR" in ctx

    def test_assemble_repair_context_includes_step_and_error(self):
        step = Step(
            order=1,
            phase=StepPhase.MUTATE,
            type=StepType.HTTP_REQUEST,
            command="POST /api/users",
            parameters={"payload": "test"},
        )
        ctx = assemble_repair_context(step, "401 Unauthorized", ["login successful"])
        assert "MUTATE" in ctx and "401 Unauthorized" in ctx

    def test_assemble_repair_context_truncates_error_log(self):
        step = Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="GET /", parameters={})
        ctx = assemble_repair_context(step, "E" * 5000, [])
        assert "[... truncated ...]" in ctx


class TestGraphTools:
    """Tests for GraphTools initialization."""

    def test_graph_tools_init_accepts_repo(self):
        if not HAS_NEO4J:
            pytest.skip("Neo4j driver unavailable")
        try:
            from llmitm_v2.tools import GraphTools
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))
            repo = GraphRepository(driver)
            tools = GraphTools(repo)
            assert tools.repo == repo
            driver.close()
        except Exception as e:
            pytest.skip(f"Neo4j or GraphDatabase unavailable: {e}")

    def test_graph_tools_lazy_loads_embedding_model(self):
        if not HAS_NEO4J:
            pytest.skip("Neo4j driver unavailable")
        try:
            from llmitm_v2.tools import GraphTools
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))
            repo = GraphRepository(driver)
            tools = GraphTools(repo)
            model = tools.embed_model
            assert model is not None
            driver.close()
        except Exception as e:
            pytest.skip(f"sentence-transformers or dependencies unavailable: {e}")


class TestAgentFactories:
    """Tests for 2-agent factory functions."""

    @pytest.mark.integration
    def test_create_recon_agent_returns_programmatic_agent(self):
        from llmitm_v2.orchestrator.agents import ProgrammaticAgent
        agent = create_recon_agent(mitm_context="demo/juice_shop.mitm")
        assert isinstance(agent, ProgrammaticAgent)

    @pytest.mark.integration
    def test_create_attack_critic_returns_simple_agent(self):
        from llmitm_v2.orchestrator.agents import SimpleAgent
        agent = create_attack_critic()
        assert isinstance(agent, SimpleAgent)

    @pytest.mark.integration
    def test_recon_agent_has_mitmdump_tool(self):
        agent = create_recon_agent(mitm_context="demo/juice_shop.mitm")
        assert "mitmdump" in agent.tool_handlers


class TestSkillGuides:
    """Tests for skill guide loading."""

    def test_load_skill_guides_returns_string(self):
        from llmitm_v2.orchestrator.agents import load_skill_guides
        guides = load_skill_guides()
        assert isinstance(guides, str) and len(guides) > 0

    def test_load_skill_guides_includes_mitmdump(self):
        from llmitm_v2.orchestrator.agents import load_skill_guides
        guides = load_skill_guides()
        assert "mitmdump" in guides.lower()
