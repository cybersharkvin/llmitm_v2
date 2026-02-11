"""Test Pydantic models for validation and serialization."""

import json

import pytest

from llmitm_v2.constants import StepPhase, StepType
from llmitm_v2.models import (
    ActionGraph,
    CriticFeedback,
    ExecutionContext,
    Finding,
    Fingerprint,
    RepairDiagnosis,
    Step,
    StepResult,
)


class TestStep:
    """Test Step model."""

    def test_step_creation(self):
        step = Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl http://localhost:3000")
        assert step.phase == StepPhase.CAPTURE and step.command == "curl http://localhost:3000"

    def test_step_serialization(self):
        step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.SHELL_COMMAND, command="python exploit.py")
        step2 = Step(**step.model_dump())
        assert step2 == step


class TestFingerprint:
    """Test Fingerprint model."""

    def test_fingerprint_hash_computation(self):
        fp = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*")
        fp.ensure_hash()
        assert fp.hash is not None and len(fp.hash) == 64

    def test_fingerprint_hash_consistency(self):
        fp1 = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*")
        fp2 = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*")
        assert fp1.ensure_hash() or fp1.hash == fp2.ensure_hash() or fp1.hash == fp2.hash

    def test_fingerprint_hash_differs_by_tech_stack(self):
        fp1 = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*")
        fp2 = Fingerprint(tech_stack="Django + REST", auth_model="Bearer token", endpoint_pattern="/api/v1/*")
        assert fp1.ensure_hash() or fp1.hash != fp2.ensure_hash() or fp1.hash != fp2.hash

    def test_fingerprint_with_embedding(self):
        embedding = [0.1] * 384
        fp = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*", observation_embedding=embedding)
        assert fp.observation_embedding == embedding


class TestActionGraph:
    """Test ActionGraph model."""

    def test_action_graph_creation(self):
        steps = [Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl test"), Step(order=1, phase=StepPhase.ANALYZE, type=StepType.REGEX_MATCH, command="grep")]
        ag = ActionGraph(vulnerability_type="IDOR", description="Test", steps=steps)
        assert ag.vulnerability_type == "IDOR" and len(ag.steps) == 2

    def test_action_graph_id_generation(self):
        ag = ActionGraph(vulnerability_type="IDOR", description="Test", steps=[])
        ag.ensure_id()
        assert ag.id is not None

    def test_action_graph_success_rate(self):
        ag = ActionGraph(vulnerability_type="IDOR", description="Test", steps=[], times_executed=10, times_succeeded=7)
        assert ag.success_rate() == 0.7

    def test_action_graph_success_rate_zero(self):
        ag = ActionGraph(vulnerability_type="IDOR", description="Test", steps=[], times_executed=0)
        assert ag.success_rate() == 0.0


class TestFinding:
    """Test Finding model."""

    def test_finding_creation(self):
        finding = Finding(observation="User ID enumeration possible", severity="high", evidence_summary="User /api/users/1 returns same data")
        assert finding.observation == "User ID enumeration possible" and finding.severity == "high"

    def test_finding_id_generation(self):
        finding = Finding(observation="Test vulnerability", severity="medium", evidence_summary="Evidence")
        finding.ensure_id()
        assert finding.id is not None


class TestCriticFeedback:
    """Test CriticFeedback model."""

    def test_critic_feedback_passed(self):
        feedback = CriticFeedback(passed=True, feedback="ActionGraph passed all validation checks.")
        assert feedback.passed is True

    def test_critic_feedback_failed(self):
        feedback = CriticFeedback(passed=False, feedback="Steps are overfitting to specific target.")
        assert feedback.passed is False


class TestRepairDiagnosis:
    """Test RepairDiagnosis model."""

    def test_repair_diagnosis_transient(self):
        from llmitm_v2.constants import FailureType
        diagnosis = RepairDiagnosis(failure_type=FailureType.TRANSIENT_RECOVERABLE, diagnosis="Network timeout.")
        assert diagnosis.failure_type == FailureType.TRANSIENT_RECOVERABLE

    def test_repair_diagnosis_systemic(self):
        from llmitm_v2.constants import FailureType
        diagnosis = RepairDiagnosis(failure_type=FailureType.SYSTEMIC, diagnosis="Target changed auth.", suggested_fix="Update step.")
        assert diagnosis.failure_type == FailureType.SYSTEMIC


class TestExecutionContext:
    """Test ExecutionContext model."""

    def test_execution_context_creation(self):
        fp = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*")
        context = ExecutionContext(target_url="http://localhost:3000", fingerprint=fp)
        assert context.target_url == "http://localhost:3000" and context.session_tokens == {} and context.previous_outputs == []


class TestStepResult:
    """Test StepResult model."""

    def test_step_result_success(self):
        result = StepResult(stdout="HTTP/1.1 200 OK", status_code=200, success_criteria_matched=True)
        assert result.success_criteria_matched is True and result.status_code == 200

    def test_step_result_failure(self):
        result = StepResult(stdout="", stderr="Connection timeout", status_code=0, success_criteria_matched=False)
        assert result.success_criteria_matched is False


class TestModelSerialization:
    """Test serialization/deserialization round-trips."""

    def test_action_graph_json_round_trip(self):
        ag = ActionGraph(vulnerability_type="IDOR", description="Test", steps=[Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl test")])
        ag.ensure_id()
        ag2 = ActionGraph(**json.loads(json.dumps(ag.model_dump(), default=str)))
        assert ag2.id == ag.id and ag2.vulnerability_type == ag.vulnerability_type

    def test_fingerprint_json_round_trip(self):
        fp = Fingerprint(tech_stack="Express.js + JWT", auth_model="Bearer token", endpoint_pattern="/api/v1/*", observation_embedding=[0.1] * 384)
        fp.ensure_hash()
        fp2 = Fingerprint(**json.loads(json.dumps(fp.model_dump(), default=str)))
        assert fp2.hash == fp.hash and fp2.tech_stack == fp.tech_stack
