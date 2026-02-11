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
        """Test basic Step creation."""
        step = Step(
            order=0,
            phase=StepPhase.CAPTURE,
            type=StepType.HTTP_REQUEST,
            command="curl http://localhost:3000",
            parameters={"method": "GET", "timeout": 5},
            success_criteria=r"HTTP/1\.1 200",
        )
        assert step.order == 0
        assert step.phase == StepPhase.CAPTURE
        assert step.type == StepType.HTTP_REQUEST
        assert step.command == "curl http://localhost:3000"
        assert step.parameters == {"method": "GET", "timeout": 5}
        assert step.success_criteria == r"HTTP/1\.1 200"
        assert step.deterministic is True

    def test_step_serialization(self):
        """Test Step model serialization/deserialization."""
        step = Step(
            order=1,
            phase=StepPhase.MUTATE,
            type=StepType.SHELL_COMMAND,
            command="python exploit.py",
            parameters={"timeout": 10},
        )
        # Serialize to dict
        step_dict = step.model_dump()
        assert step_dict["order"] == 1
        assert step_dict["phase"] == "MUTATE"
        # Deserialize back
        step2 = Step(**step_dict)
        assert step2 == step


class TestFingerprint:
    """Test Fingerprint model."""

    def test_fingerprint_hash_computation(self):
        """Test Fingerprint hash computation."""
        fp = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
        )
        fp.ensure_hash()
        assert fp.hash is not None
        assert len(fp.hash) == 64  # SHA256 hexdigest length

    def test_fingerprint_hash_consistency(self):
        """Test that identical fingerprints produce same hash."""
        fp1 = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
        )
        fp1.ensure_hash()

        fp2 = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
        )
        fp2.ensure_hash()

        assert fp1.hash == fp2.hash

    def test_fingerprint_hash_differs_by_tech_stack(self):
        """Test that different tech stacks produce different hashes."""
        fp1 = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
        )
        fp1.ensure_hash()

        fp2 = Fingerprint(
            tech_stack="Django + REST",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
        )
        fp2.ensure_hash()

        assert fp1.hash != fp2.hash

    def test_fingerprint_with_embedding(self):
        """Test Fingerprint with observation embedding."""
        embedding = [0.1] * 384
        fp = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
            observation_embedding=embedding,
        )
        assert fp.observation_embedding == embedding
        assert len(fp.observation_embedding) == 384


class TestActionGraph:
    """Test ActionGraph model."""

    def test_action_graph_creation(self):
        """Test ActionGraph creation."""
        steps = [
            Step(
                order=0,
                phase=StepPhase.CAPTURE,
                type=StepType.HTTP_REQUEST,
                command="curl http://localhost:3000",
            ),
            Step(
                order=1,
                phase=StepPhase.ANALYZE,
                type=StepType.REGEX_MATCH,
                command="grep 'user_id'",
            ),
        ]
        ag = ActionGraph(
            vulnerability_type="IDOR",
            description="Test user enumeration via ID parameter",
            steps=steps,
        )
        assert ag.vulnerability_type == "IDOR"
        assert len(ag.steps) == 2
        assert ag.times_executed == 0
        assert ag.times_succeeded == 0

    def test_action_graph_id_generation(self):
        """Test ActionGraph ID generation."""
        ag = ActionGraph(
            vulnerability_type="IDOR",
            description="Test",
            steps=[],
        )
        assert ag.id is None
        ag.ensure_id()
        assert ag.id is not None

    def test_action_graph_success_rate(self):
        """Test ActionGraph success rate computation."""
        ag = ActionGraph(
            vulnerability_type="IDOR",
            description="Test",
            steps=[],
            times_executed=10,
            times_succeeded=7,
        )
        assert ag.success_rate() == 0.7

    def test_action_graph_success_rate_zero(self):
        """Test ActionGraph success rate when not executed."""
        ag = ActionGraph(
            vulnerability_type="IDOR",
            description="Test",
            steps=[],
            times_executed=0,
        )
        assert ag.success_rate() == 0.0


class TestFinding:
    """Test Finding model."""

    def test_finding_creation(self):
        """Test Finding creation."""
        finding = Finding(
            observation="User ID enumeration possible",
            severity="high",
            evidence_summary="User /api/users/1 returns same data structure for all IDs",
            target_url="http://localhost:3000",
        )
        assert finding.observation == "User ID enumeration possible"
        assert finding.severity == "high"

    def test_finding_id_generation(self):
        """Test Finding ID generation."""
        finding = Finding(
            observation="Test vulnerability",
            severity="medium",
            evidence_summary="Evidence",
        )
        assert finding.id is None
        finding.ensure_id()
        assert finding.id is not None


class TestCriticFeedback:
    """Test CriticFeedback model."""

    def test_critic_feedback_passed(self):
        """Test CriticFeedback for passing validation."""
        feedback = CriticFeedback(
            passed=True,
            feedback="ActionGraph passed all validation checks.",
        )
        assert feedback.passed is True

    def test_critic_feedback_failed(self):
        """Test CriticFeedback for failing validation."""
        feedback = CriticFeedback(
            passed=False,
            feedback="Steps are overfitting to specific target. Generalize endpoint patterns.",
        )
        assert feedback.passed is False


class TestRepairDiagnosis:
    """Test RepairDiagnosis model."""

    def test_repair_diagnosis_transient(self):
        """Test RepairDiagnosis for transient failures."""
        from llmitm_v2.constants import FailureType

        diagnosis = RepairDiagnosis(
            failure_type=FailureType.TRANSIENT_RECOVERABLE,
            diagnosis="Network timeout, will retry immediately.",
        )
        assert diagnosis.failure_type == FailureType.TRANSIENT_RECOVERABLE

    def test_repair_diagnosis_systemic(self):
        """Test RepairDiagnosis for systemic failures."""
        from llmitm_v2.constants import FailureType

        diagnosis = RepairDiagnosis(
            failure_type=FailureType.SYSTEMIC,
            diagnosis="Target changed authentication mechanism.",
            suggested_fix="Update step to use new API token endpoint.",
        )
        assert diagnosis.failure_type == FailureType.SYSTEMIC
        assert diagnosis.suggested_fix is not None


class TestExecutionContext:
    """Test ExecutionContext model."""

    def test_execution_context_creation(self):
        """Test ExecutionContext creation."""
        fp = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
        )
        context = ExecutionContext(
            target_url="http://localhost:3000",
            fingerprint=fp,
        )
        assert context.target_url == "http://localhost:3000"
        assert context.session_tokens == {}
        assert context.previous_outputs == []


class TestStepResult:
    """Test StepResult model."""

    def test_step_result_success(self):
        """Test successful StepResult."""
        result = StepResult(
            stdout="HTTP/1.1 200 OK",
            status_code=200,
            success_criteria_matched=True,
        )
        assert result.success_criteria_matched is True
        assert result.status_code == 200

    def test_step_result_failure(self):
        """Test failed StepResult."""
        result = StepResult(
            stdout="",
            stderr="Connection timeout",
            status_code=0,
            success_criteria_matched=False,
        )
        assert result.success_criteria_matched is False


class TestModelSerialization:
    """Test serialization/deserialization round-trips."""

    def test_action_graph_json_round_trip(self):
        """Test ActionGraph JSON serialization."""
        steps = [
            Step(
                order=0,
                phase=StepPhase.CAPTURE,
                type=StepType.HTTP_REQUEST,
                command="curl test",
                parameters={"timeout": 5},
            )
        ]
        ag = ActionGraph(
            vulnerability_type="IDOR",
            description="Test",
            steps=steps,
        )
        ag.ensure_id()

        # Serialize
        ag_dict = ag.model_dump()
        json_str = json.dumps(ag_dict, default=str)

        # Deserialize
        ag_dict2 = json.loads(json_str)
        ag2 = ActionGraph(**ag_dict2)

        assert ag2.id == ag.id
        assert ag2.vulnerability_type == ag.vulnerability_type
        assert len(ag2.steps) == 1
        assert ag2.steps[0].command == "curl test"

    def test_fingerprint_json_round_trip(self):
        """Test Fingerprint JSON serialization."""
        fp = Fingerprint(
            tech_stack="Express.js + JWT",
            auth_model="Bearer token",
            endpoint_pattern="/api/v1/*",
            security_signals=["CORS enabled"],
            observation_embedding=[0.1] * 384,
        )
        fp.ensure_hash()

        # Serialize
        fp_dict = fp.model_dump()
        json_str = json.dumps(fp_dict, default=str)

        # Deserialize
        fp_dict2 = json.loads(json_str)
        fp2 = Fingerprint(**fp_dict2)

        assert fp2.hash == fp.hash
        assert fp2.tech_stack == fp.tech_stack
        assert len(fp2.observation_embedding) == 384
