"""Main orchestration loop: cold start, warm start, and self-repair."""

import logging
import re
from typing import Optional

try:
    from strands.types.exceptions import StructuredOutputException
except ImportError:
    StructuredOutputException = Exception  # type: ignore

from llmitm_v2.config import Settings
from llmitm_v2.constants import FailureType
from llmitm_v2.handlers.registry import get_handler
from llmitm_v2.models import (
    ActionGraph,
    CriticFeedback,
    ExecutionContext,
    ExecutionResult,
    Finding,
    Fingerprint,
    OrchestratorResult,
    RepairDiagnosis,
    Step,
    StepResult,
)
from llmitm_v2.orchestrator.agents import create_actor_agent, create_critic_agent
from llmitm_v2.orchestrator.context import (
    assemble_compilation_context,
    assemble_repair_context,
)
from llmitm_v2.orchestrator.failure_classifier import classify_failure
from llmitm_v2.repository import GraphRepository

logger = logging.getLogger(__name__)

# Regex for {{previous_outputs[N]}} interpolation
_INTERPOLATION_RE = re.compile(r"\{\{previous_outputs\[(-?\d+)\]\}\}")


class Orchestrator:
    """Main orchestration loop: decides cold/warm start, executes, handles repair."""

    def __init__(self, graph_repo: GraphRepository, settings: Settings):
        self.graph_repo = graph_repo
        self.settings = settings

    def run(self, fingerprint: Fingerprint, traffic_log: str) -> OrchestratorResult:
        """Main entry point. Decides cold vs warm start, executes, handles repair."""
        fingerprint.ensure_hash()
        self.graph_repo.save_fingerprint(fingerprint)

        ag = self._try_warm_start(fingerprint)
        compiled = False
        if ag is None:
            ag = self._compile(fingerprint, traffic_log)
            compiled = True

        result = self._execute(ag, fingerprint)
        self.graph_repo.increment_execution_count(ag.id, result.success)

        return OrchestratorResult(
            path="cold_start" if compiled else "warm_start",
            action_graph_id=ag.id,
            execution=result,
            compiled=compiled,
            repaired=False,
        )

    def _try_warm_start(self, fingerprint: Fingerprint) -> Optional[ActionGraph]:
        """Lookup existing ActionGraph by fingerprint hash."""
        data = self.graph_repo.get_action_graph_with_steps(fingerprint.hash)
        if data is None:
            return None
        return ActionGraph(**data)

    def _compile(self, fingerprint: Fingerprint, traffic_log: str) -> ActionGraph:
        """Actor/Critic loop -> validated ActionGraph -> save to Neo4j."""
        context = assemble_compilation_context(fingerprint, traffic_log)
        actor = create_actor_agent(self.graph_repo)
        critic = create_critic_agent()

        for i in range(self.settings.max_critic_iterations):
            try:
                actor_result = actor(context, structured_output_model=ActionGraph)
                ag = actor_result.structured_output
            except StructuredOutputException:
                logger.warning("Actor structured output failed on iteration %d", i)
                continue

            try:
                critic_result = critic(
                    ag.model_dump_json(), structured_output_model=CriticFeedback
                )
                feedback = critic_result.structured_output
            except StructuredOutputException:
                logger.warning("Critic structured output failed on iteration %d", i)
                continue

            if feedback.passed:
                ag.ensure_id()
                self.graph_repo.save_action_graph(fingerprint.hash, ag)
                return ag

            context += f"\n\nCritic feedback: {feedback.feedback}"

        raise RuntimeError(
            f"Compilation failed after {self.settings.max_critic_iterations} iterations"
        )

    def _execute(
        self, action_graph: ActionGraph, fingerprint: Fingerprint
    ) -> ExecutionResult:
        """Walk steps, dispatch to handlers, thread context, collect findings."""
        ctx = ExecutionContext(
            target_url=self.settings.target_url, fingerprint=fingerprint
        )
        findings: list[Finding] = []
        steps_executed = 0
        repaired = False

        sorted_steps = sorted(action_graph.steps, key=lambda s: s.order)

        for step in sorted_steps:
            interpolated = self._interpolate_params(step, ctx)
            handler = get_handler(interpolated.type)
            result = handler.execute(interpolated, ctx)
            steps_executed += 1
            ctx.previous_outputs.append(result.stdout)

            # Check for finding
            if result.success_criteria_matched and step.success_criteria:
                finding = Finding(
                    observation=f"Success criteria matched at step {step.order}",
                    severity="medium",
                    evidence_summary=result.stdout[:500],
                    target_url=self.settings.target_url,
                )
                finding.ensure_id()
                self.graph_repo.save_finding(action_graph.id, finding)
                findings.append(finding)

            # Check for failure
            step_failed = result.stderr or (
                step.success_criteria and not result.success_criteria_matched
            )
            if step_failed:
                action = self._handle_step_failure(
                    step, result, ctx, action_graph, retried=False
                )
                if action == "abort":
                    return ExecutionResult(
                        success=False,
                        findings=findings,
                        steps_executed=steps_executed,
                        error_log=result.stderr or result.stdout,
                    )
                if action == "repaired":
                    repaired = True

        return ExecutionResult(
            success=True, findings=findings, steps_executed=steps_executed
        )

    def _handle_step_failure(
        self,
        step: Step,
        result: StepResult,
        context: ExecutionContext,
        action_graph: ActionGraph,
        retried: bool,
    ) -> str:
        """Classify failure -> 'retry' / 'abort' / 'repaired'. Returns action taken."""
        error_log = result.stderr or result.stdout
        failure_type = classify_failure(error_log, result.status_code or 0)

        if failure_type == FailureType.TRANSIENT_RECOVERABLE and not retried:
            # Retry once
            handler = get_handler(step.type)
            retry_result = handler.execute(step, context)
            if not retry_result.stderr:
                context.previous_outputs.append(retry_result.stdout)
                return "retry"
            # Escalate to systemic on retry failure
            failure_type = FailureType.SYSTEMIC

        if failure_type == FailureType.TRANSIENT_UNRECOVERABLE:
            return "abort"

        if failure_type == FailureType.SYSTEMIC:
            try:
                self._repair(
                    action_graph,
                    step,
                    error_log,
                    context.previous_outputs,
                )
                return "repaired"
            except Exception:
                logger.exception("Repair failed for step %d", step.order)
                return "abort"

        return "abort"

    @staticmethod
    def _interpolate_params(step: Step, context: ExecutionContext) -> Step:
        """Replace {{previous_outputs[N]}} in step parameters with actual values."""
        new_params = {}
        for key, value in step.parameters.items():
            if isinstance(value, str) and "{{previous_outputs[" in value:

                def replacer(match: re.Match) -> str:
                    idx = int(match.group(1))
                    try:
                        return context.previous_outputs[idx]
                    except IndexError:
                        return match.group(0)

                new_params[key] = _INTERPOLATION_RE.sub(replacer, value)
            else:
                new_params[key] = value

        return step.model_copy(update={"parameters": new_params})

    def _repair(
        self,
        action_graph: ActionGraph,
        failed_step: Step,
        error_log: str,
        execution_history: list[str],
    ) -> ActionGraph:
        """LLM diagnoses systemic failure, repairs step chain in Neo4j."""
        context = assemble_repair_context(failed_step, error_log, execution_history)
        actor = create_actor_agent(self.graph_repo)

        try:
            repair_result = actor(
                context, structured_output_model=RepairDiagnosis
            )
            diagnosis = repair_result.structured_output
        except StructuredOutputException:
            raise RuntimeError("Repair diagnosis failed: structured output error")

        if diagnosis.suggested_fix:
            new_step = Step(
                order=failed_step.order,
                phase=failed_step.phase,
                type=failed_step.type,
                command=diagnosis.suggested_fix,
                parameters=failed_step.parameters,
                success_criteria=failed_step.success_criteria,
            )
            self.graph_repo.repair_step_chain(
                action_graph.id, failed_step.order, [new_step]
            )

        # Re-fetch updated graph
        data = self.graph_repo.get_action_graph_with_steps(
            action_graph.id  # This needs fingerprint hash, not AG id
        )
        return ActionGraph(**data) if data else action_graph
