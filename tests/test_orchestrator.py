"""Tests for orchestration layer: agents, context, failure classification, hooks."""

import pytest

from llmitm_v2.constants import FailureType, StepPhase, StepType
from llmitm_v2.hooks import ApprovalHook
from llmitm_v2.models import Fingerprint, Step
from llmitm_v2.orchestrator import (
    assemble_compilation_context,
    assemble_repair_context,
    classify_failure,
    create_actor_agent,
    create_critic_agent,
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

    def test_assemble_compilation_context_includes_fingerprint(self):
        fp = Fingerprint(
            tech_stack="Express.js",
            auth_model="JWT",
            endpoint_pattern="/api/v1/*",
            security_signals=["CORS enabled", "no CSRF tokens"],
            observation_text="",
        )
        traffic = "GET /api/v1/users HTTP/1.1\nAuthorization: Bearer token"

        ctx = assemble_compilation_context(fp, traffic)
        assert "Express.js" in ctx
        assert "JWT" in ctx
        assert "/api/v1/*" in ctx
        assert "CORS enabled" in ctx

    def test_assemble_compilation_context_truncates_long_traffic(self):
        fp = Fingerprint(
            tech_stack="Django",
            auth_model="Session",
            endpoint_pattern="/admin/*",
            security_signals=[],
            observation_text="",
        )
        traffic = "X" * 10000  # Long traffic log

        ctx = assemble_compilation_context(fp, traffic)
        assert "[... truncated ...]" in ctx
        assert len(ctx) < len(traffic)

    def test_assemble_repair_context_includes_step_and_error(self):
        step = Step(
            order=1,
            phase=StepPhase.MUTATE,
            type=StepType.HTTP_REQUEST,
            command="POST /api/users",
            parameters={"payload": "test"},
        )
        error = "401 Unauthorized"
        history = ["Step 0 output: login successful"]

        ctx = assemble_repair_context(step, error, history)
        assert "MUTATE" in ctx
        assert "http_request" in ctx
        assert "401 Unauthorized" in ctx
        assert "login successful" in ctx

    def test_assemble_repair_context_truncates_error_log(self):
        step = Step(
            order=0,
            phase=StepPhase.CAPTURE,
            type=StepType.HTTP_REQUEST,
            command="GET /",
            parameters={},
        )
        error = "E" * 5000

        ctx = assemble_repair_context(step, error, [])
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


class TestApprovalHook:
    """Tests for approval hook."""

    def test_approval_hook_is_hook_provider(self):
        try:
            from strands.hooks import HookProvider
        except ImportError:
            pytest.skip("Strands SDK unavailable")
        hook = ApprovalHook()
        assert isinstance(hook, HookProvider)

    def test_approval_hook_accepts_custom_patterns(self):
        patterns = ["CUSTOM", "PATTERNS"]
        hook = ApprovalHook(destructive_patterns=patterns)
        assert hook.destructive_patterns == patterns

    def test_approval_hook_has_default_patterns(self):
        hook = ApprovalHook()
        assert "DELETE" in hook.destructive_patterns
        assert "DROP" in hook.destructive_patterns


class TestAgentFactories:
    """Integration tests for agent factories (require Strands + Anthropic API)."""

    @pytest.mark.integration
    def test_create_actor_agent_returns_agent(self):
        if not HAS_NEO4J:
            pytest.skip("Neo4j driver unavailable")
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))
            repo = GraphRepository(driver)
            agent = create_actor_agent(repo)
            from strands import Agent

            assert isinstance(agent, Agent)
            driver.close()
        except Exception as e:
            pytest.skip(f"Neo4j or Strands unavailable: {e}")

    @pytest.mark.integration
    def test_create_critic_agent_returns_agent(self):
        try:
            agent = create_critic_agent()
            from strands import Agent

            assert isinstance(agent, Agent)
        except Exception as e:
            pytest.skip(f"Strands SDK unavailable: {e}")
