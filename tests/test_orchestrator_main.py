"""Tests for Orchestrator main loop, ExecutionResult, and OrchestratorResult."""

import pytest

from llmitm_v2.constants import StepPhase, StepType
from llmitm_v2.models import (
    ExecutionContext,
    ExecutionResult,
    Fingerprint,
    OrchestratorResult,
    Step,
)
from llmitm_v2.orchestrator.orchestrator import Orchestrator

try:
    from llmitm_v2.repository import GraphRepository

    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False


# --- Fixtures ---


@pytest.fixture
def fingerprint():
    return Fingerprint(
        tech_stack="Express.js",
        auth_model="JWT",
        endpoint_pattern="/api/*",
        security_signals=["CORS enabled"],
    )


@pytest.fixture
def sample_step():
    return Step(
        order=0,
        phase=StepPhase.CAPTURE,
        type=StepType.HTTP_REQUEST,
        command="GET /api/health",
    )


# --- ExecutionResult tests ---


class TestExecutionResult:
    def test_defaults(self):
        result = ExecutionResult(success=True)
        assert result.findings == [] and result.steps_executed == 0 and result.error_log is None

    def test_with_error(self):
        result = ExecutionResult(success=False, error_log="404 Not Found", steps_executed=3)
        assert not result.success and result.steps_executed == 3


# --- OrchestratorResult tests ---


class TestOrchestratorResult:
    def test_cold_start_path(self):
        result = OrchestratorResult(path="cold_start", compiled=True, action_graph_id="ag-1")
        assert result.path == "cold_start" and result.compiled is True

    def test_warm_start_path(self):
        result = OrchestratorResult(path="warm_start", compiled=False, action_graph_id="ag-1")
        assert result.path == "warm_start" and result.compiled is False

    def test_with_execution_result(self):
        ex = ExecutionResult(success=True, steps_executed=5)
        result = OrchestratorResult(path="warm_start", execution=ex)
        assert result.execution.success and result.execution.steps_executed == 5


# --- Orchestrator construction ---


class TestOrchestratorInit:
    @pytest.mark.skipif(not HAS_NEO4J, reason="neo4j not installed")
    def test_init_stores_dependencies(self):
        pytest.skip("Neo4j driver required")


# --- Interpolation tests ---


class TestInterpolateParams:
    def test_replaces_previous_output_reference(self, fingerprint):
        step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.HTTP_REQUEST, command="POST /api", parameters={"body": "token={{previous_outputs[0]}}"})
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint, previous_outputs=["abc123"])
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["body"] == "token=abc123"

    def test_negative_index(self, fingerprint):
        step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.HTTP_REQUEST, command="POST /api", parameters={"auth": "Bearer {{previous_outputs[-1]}}"})
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint, previous_outputs=["first", "second"])
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["auth"] == "Bearer second"

    def test_no_interpolation_needed(self, fingerprint):
        step = Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="GET /", parameters={"url": "/api/health"})
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint)
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["url"] == "/api/health"

    def test_preserves_non_string_values(self, fingerprint):
        step = Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="GET /", parameters={"timeout": 30})
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint)
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["timeout"] == 30

    def test_out_of_range_index_preserved(self, fingerprint):
        step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.HTTP_REQUEST, command="POST /", parameters={"x": "{{previous_outputs[99]}}"})
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint, previous_outputs=["only"])
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["x"] == "{{previous_outputs[99]}}"

    def test_recursive_interpolation_nested_dict(self, fingerprint):
        params = {"headers": {"Authorization": "Bearer {{previous_outputs[0]}}"}}
        step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.HTTP_REQUEST, command="GET /", parameters=params)
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint, previous_outputs=["token123"])
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["headers"]["Authorization"] == "Bearer token123"

    def test_recursive_interpolation_nested_list(self, fingerprint):
        params = {"values": ["prefix-{{previous_outputs[0]}}", "suffix"]}
        step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.HTTP_REQUEST, command="GET /", parameters=params)
        ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint, previous_outputs=["xyz"])
        result = Orchestrator._interpolate_params(step, ctx)
        assert result.parameters["values"][0] == "prefix-xyz" and result.parameters["values"][1] == "suffix"
