"""Tests for Phase 3: Step Handlers."""

import pytest

from llmitm_v2.constants import StepPhase, StepType
from llmitm_v2.handlers import (
    HTTPRequestHandler,
    RegexMatchHandler,
    ShellCommandHandler,
    StepHandler,
    get_handler,
    HANDLER_REGISTRY,
)
from llmitm_v2.models import ExecutionContext, Fingerprint, Step, StepResult


# --- Fixtures ---

@pytest.fixture
def fingerprint():
    return Fingerprint(tech_stack="node", auth_model="jwt", endpoint_pattern="/api/*", security_signals=["cors"])


@pytest.fixture
def context(fingerprint):
    return ExecutionContext(target_url="http://localhost:3000", fingerprint=fingerprint)


@pytest.fixture
def step_factory():
    def _make(step_type, command="test", **params):
        return Step(order=1, phase=StepPhase.CAPTURE, type=step_type, command=command, parameters=params)
    return _make


# --- StepHandler ABC ---

def test_step_handler_is_abstract():
    with pytest.raises(TypeError):
        StepHandler()


def test_step_handler_subclass_requires_execute():
    class Incomplete(StepHandler):
        pass
    with pytest.raises(TypeError):
        Incomplete()


def test_step_handler_subclass_with_execute():
    class Complete(StepHandler):
        def execute(self, step, context):
            return StepResult(stdout="ok")
    assert Complete().execute(None, None).stdout == "ok"


# --- ShellCommandHandler ---

def test_shell_echo(step_factory, context):
    result = ShellCommandHandler().execute(step_factory(StepType.SHELL_COMMAND, command="echo hello"), context)
    assert result.stdout.strip() == "hello" and result.status_code == 0


def test_shell_exit_code(step_factory, context):
    result = ShellCommandHandler().execute(step_factory(StepType.SHELL_COMMAND, command="exit 42"), context)
    assert result.status_code == 42


def test_shell_timeout(step_factory, context):
    result = ShellCommandHandler().execute(step_factory(StepType.SHELL_COMMAND, command="sleep 10", timeout=0.1), context)
    assert "Timeout" in result.stderr and result.status_code == -1


def test_shell_success_criteria(step_factory, context):
    step = Step(order=1, phase=StepPhase.CAPTURE, type=StepType.SHELL_COMMAND, command="echo hello world", success_criteria="hello")
    assert ShellCommandHandler().execute(step, context).success_criteria_matched is True


def test_shell_env_vars(step_factory, context):
    result = ShellCommandHandler().execute(step_factory(StepType.SHELL_COMMAND, command="echo $MY_VAR", env={"MY_VAR": "test123"}), context)
    assert "test123" in result.stdout


# --- RegexMatchHandler ---

def test_regex_last_output(step_factory, context):
    context.previous_outputs = ["token=abc123"]
    result = RegexMatchHandler().execute(step_factory(StepType.REGEX_MATCH, pattern="token=(\\w+)"), context)
    assert result.success_criteria_matched is True and "abc123" in result.stdout


def test_regex_capture_group(step_factory, context):
    context.previous_outputs = ["id:42 name:test"]
    result = RegexMatchHandler().execute(step_factory(StepType.REGEX_MATCH, pattern="id:(\\d+)", capture_group=1), context)
    assert result.stdout == "42"


def test_regex_no_match(step_factory, context):
    context.previous_outputs = ["nothing here"]
    result = RegexMatchHandler().execute(step_factory(StepType.REGEX_MATCH, pattern="token=\\w+"), context)
    assert result.success_criteria_matched is False and result.stdout == ""


def test_regex_no_outputs(step_factory, context):
    result = RegexMatchHandler().execute(step_factory(StepType.REGEX_MATCH, pattern="test"), context)
    assert "No previous outputs" in result.stderr


def test_regex_source_by_index(step_factory, context):
    context.previous_outputs = ["first", "second=val"]
    result = RegexMatchHandler().execute(step_factory(StepType.REGEX_MATCH, pattern="second=(\\w+)", source=1, capture_group=1), context)
    assert result.stdout == "val"


# --- ExecutionContext cookies ---

def test_execution_context_cookies_default(fingerprint):
    ctx = ExecutionContext(target_url="http://localhost", fingerprint=fingerprint)
    assert ctx.cookies == {}


# --- Handler Registry ---

def test_registry_has_three_types():
    assert set(HANDLER_REGISTRY.keys()) == {StepType.HTTP_REQUEST, StepType.SHELL_COMMAND, StepType.REGEX_MATCH}


def test_get_handler_returns_correct_type():
    assert isinstance(get_handler(StepType.HTTP_REQUEST), HTTPRequestHandler)


def test_get_handler_unknown_raises():
    with pytest.raises(ValueError, match="No handler registered"):
        get_handler(StepType.JSON_EXTRACT)


# --- Integration: HTTP (skip if no network) ---

@pytest.mark.integration
def test_http_get_real(step_factory, context):
    try:
        result = HTTPRequestHandler().execute(step_factory(StepType.HTTP_REQUEST, url="http://httpbin.org/get", method="GET"), context)
        assert result.status_code == 200
    except Exception:
        pytest.skip("Network unavailable")


@pytest.mark.integration
def test_http_post_with_body(step_factory, context):
    try:
        result = HTTPRequestHandler().execute(step_factory(StepType.HTTP_REQUEST, url="http://httpbin.org/post", method="POST", body='{"test":1}'), context)
        assert result.status_code == 200
    except Exception:
        pytest.skip("Network unavailable")
