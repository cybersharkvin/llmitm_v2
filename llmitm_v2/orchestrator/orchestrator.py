"""Main orchestration loop: cold start, warm start, and self-repair.

Uses 2-agent architecture:
- Recon Agent (ProgrammaticAgent): explores target via code_execution + recon tools
- Attack Critic (SimpleAgent): adversarially refines the attack plan
"""

import logging
import re
from typing import Optional

from llmitm_v2.config import Settings
from llmitm_v2.constants import FailureType, StepPhase
from llmitm_v2.debug_logger import log_event
from llmitm_v2.handlers.registry import get_handler
from llmitm_v2.models import (
    ActionGraph,
    ExecutionContext,
    ExecutionResult,
    Finding,
    Fingerprint,
    OrchestratorResult,
    Step,
    StepResult,
)
from llmitm_v2.models.recon import AttackPlan
from llmitm_v2.orchestrator.agents import create_attack_critic, create_recon_agent
from llmitm_v2.orchestrator.context import (
    assemble_recon_context,
    assemble_repair_context,
)
from llmitm_v2.orchestrator.failure_classifier import classify_failure
from llmitm_v2.repository import GraphRepository
from llmitm_v2.tools.exploit_tools import EXPLOIT_STEP_GENERATORS

logger = logging.getLogger(__name__)

# Regex for {{previous_outputs[N]}} interpolation
_INTERPOLATION_RE = re.compile(r"\{\{previous_outputs\[(-?\d+)\]\}\}")


def attack_plan_to_action_graph(plan: AttackPlan) -> ActionGraph:
    """Convert a refined AttackPlan into an executable ActionGraph.

    Each opportunity's recommended_exploit maps to a step generator.
    Steps are concatenated in priority order with sequential numbering.
    This is deterministic — no LLM involved.
    """
    all_steps: list[Step] = []
    order = 1
    for opp in plan.attack_plan[:1]:  # Hard cap: 1 exploit per graph
        generator = EXPLOIT_STEP_GENERATORS[opp.recommended_exploit]
        steps = generator(opp.exploit_target, opp.observation)
        for step in steps:
            step.order = order
            all_steps.append(step)
            order += 1
    return ActionGraph(
        vulnerability_type=plan.attack_plan[0].opportunity if plan.attack_plan else "unknown",
        description=f"Auto-generated from AttackPlan with {len(plan.attack_plan)} opportunities",
        steps=all_steps,
    )


class Orchestrator:
    """Main orchestration loop: decides cold/warm start, executes, handles repair."""

    def __init__(self, graph_repo: GraphRepository, settings: Settings):
        self.graph_repo = graph_repo
        self.settings = settings

    def run(
        self,
        fingerprint: Fingerprint,
        mitm_file: str = "",
        proxy_url: str = "",
    ) -> OrchestratorResult:
        """Main entry point. Decides cold vs warm start, executes, handles repair.

        Args:
            fingerprint: Target fingerprint for Neo4j lookup
            mitm_file: Path to .mitm capture file (file mode)
            proxy_url: Live proxy URL (live mode)
        """
        fingerprint.ensure_hash()
        self.graph_repo.save_fingerprint(fingerprint)
        self._mitm_file = mitm_file
        self._proxy_url = proxy_url

        ag = self._try_warm_start(fingerprint)
        compiled = False
        if ag is None:
            ag = self._compile(fingerprint, mitm_file=mitm_file, proxy_url=proxy_url)
            compiled = True

        result = self._execute(ag, fingerprint)
        self.graph_repo.increment_execution_count(ag.id, result.success)

        path = "repair" if result.repaired else ("cold_start" if compiled else "warm_start")
        return OrchestratorResult(
            path=path,
            action_graph_id=ag.id,
            execution=result,
            compiled=compiled,
            repaired=result.repaired,
        )

    def _try_warm_start(self, fingerprint: Fingerprint) -> Optional[ActionGraph]:
        """Lookup existing ActionGraph by fingerprint hash."""
        data = self.graph_repo.get_action_graph_with_steps(fingerprint.hash)
        if data is None:
            return None
        return ActionGraph(**data)

    def _compile(
        self,
        fingerprint: Fingerprint,
        mitm_file: str = "",
        proxy_url: str = "",
        repair_context: str = "",
    ) -> ActionGraph:
        """Recon Agent -> Attack Critic -> AttackPlan -> ActionGraph -> save to Neo4j.

        The Recon Agent produces an AttackPlan (structured output).
        The Attack Critic refines it (same schema).
        attack_plan_to_action_graph() converts deterministically to ActionGraph.

        Args:
            repair_context: If non-empty, prepended to recon context with failure details.
        """
        if mitm_file:
            mitm_context = f"Pre-recorded capture file: {mitm_file}"
        elif proxy_url:
            mitm_context = f"Live proxy: {proxy_url}"
        else:
            mitm_context = "No target context available."

        recon = create_recon_agent(
            mitm_context=mitm_context,
            model_id=self.settings.model_id,
            api_key=self.settings.anthropic_api_key,
        )
        critic = create_attack_critic(
            model_id=self.settings.model_id,
            api_key=self.settings.anthropic_api_key,
        )

        context = assemble_recon_context(mitm_file=mitm_file, proxy_url=proxy_url)
        if repair_context:
            context = repair_context + context

        for i in range(self.settings.max_critic_iterations):
            log_event("compile_iter", {"iteration": i})
            try:
                recon_result = recon(context, structured_output_model=AttackPlan)
                plan = recon_result.structured_output
            except Exception as e:
                logger.warning("Recon agent failed on iteration %d: %s: %s", i, type(e).__name__, e)
                continue

            try:
                critic_result = critic(
                    plan.model_dump_json(), structured_output_model=AttackPlan
                )
                refined_plan = critic_result.structured_output
            except Exception as e:
                logger.warning("Attack critic failed on iteration %d: %s: %s", i, type(e).__name__, e)
                continue

            log_event("critic_result", {
                "opportunities": len(refined_plan.attack_plan),
                "exploits": [o.recommended_exploit for o in refined_plan.attack_plan],
            })

            ag = attack_plan_to_action_graph(refined_plan)
            ag.ensure_id()
            self.graph_repo.save_action_graph(fingerprint.hash, ag)
            return ag

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

        i = 0
        while i < len(sorted_steps):
            step = sorted_steps[i]
            interpolated = self._interpolate_params(step, ctx)
            handler = get_handler(interpolated.type)
            result = handler.execute(interpolated, ctx)
            steps_executed += 1
            log_event("step_result", {"order": step.order, "type": step.type if isinstance(step.type, str) else step.type.value, "matched": result.success_criteria_matched})

            # Check for finding
            if result.success_criteria_matched and step.success_criteria and step.phase == StepPhase.OBSERVE:
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
                if repaired:
                    # Already repaired once this run — abort to avoid runaway repairs
                    return ExecutionResult(
                        success=False, findings=findings,
                        steps_executed=steps_executed,
                        error_log=result.stderr or result.stdout, repaired=repaired,
                    )
                action = self._handle_step_failure(
                    step, result, ctx, action_graph, retried=False
                )
                if action == "abort":
                    return ExecutionResult(
                        success=False,
                        findings=findings,
                        steps_executed=steps_executed,
                        error_log=result.stderr or result.stdout,
                        repaired=repaired,
                    )
                if isinstance(action, tuple) and action[0] == "repaired":
                    repaired = True
                    new_ag = action[1]
                    sorted_steps = sorted(new_ag.steps, key=lambda s: s.order)
                    action_graph = new_ag
                    ctx = ExecutionContext(
                        target_url=self.settings.target_url, fingerprint=fingerprint
                    )
                    i = 0
                    continue  # Restart from step 0 with new graph
            else:
                ctx.previous_outputs.append(result.stdout)

            i += 1

        return ExecutionResult(
            success=True, findings=findings, steps_executed=steps_executed, repaired=repaired
        )

    def _handle_step_failure(
        self,
        step: Step,
        result: StepResult,
        context: ExecutionContext,
        action_graph: ActionGraph,
        retried: bool,
    ) -> "str | tuple[str, ActionGraph]":
        """Classify failure -> 'retry' / 'abort' / ('repaired', new_ag). Returns action taken."""
        error_log = result.stderr or result.stdout
        failure_type = classify_failure(error_log, result.status_code or 0)
        log_event("failure", {"step": step.order, "type": failure_type.value})

        if failure_type == FailureType.TRANSIENT_RECOVERABLE and not retried:
            handler = get_handler(step.type)
            retry_result = handler.execute(step, context)
            if not retry_result.stderr:
                context.previous_outputs.append(retry_result.stdout)
                return "retry"
            failure_type = FailureType.SYSTEMIC

        if failure_type == FailureType.TRANSIENT_UNRECOVERABLE:
            return "abort"

        if failure_type == FailureType.SYSTEMIC:
            try:
                new_ag = self._repair(
                    action_graph,
                    step,
                    error_log,
                    context.previous_outputs,
                    context.fingerprint,
                )
                return ("repaired", new_ag)
            except Exception:
                logger.exception("Repair failed for step %d", step.order)
                return "abort"

        return "abort"

    @staticmethod
    def _interpolate_params(step: Step, context: ExecutionContext) -> Step:
        """Replace {{previous_outputs[N]}} in step parameters with actual values (recursive)."""
        def replacer(match: re.Match) -> str:
            idx = int(match.group(1))
            try:
                return context.previous_outputs[idx]
            except IndexError:
                return match.group(0)

        def interpolate_value(value: object) -> object:
            if isinstance(value, str) and "{{previous_outputs[" in value:
                return _INTERPOLATION_RE.sub(replacer, value)
            elif isinstance(value, dict):
                return {k: interpolate_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [interpolate_value(v) for v in value]
            else:
                return value

        new_params = {k: interpolate_value(v) for k, v in step.parameters.items()}
        return step.model_copy(update={"parameters": new_params})

    def _repair(
        self,
        action_graph: ActionGraph,
        failed_step: Step,
        error_log: str,
        execution_history: list[str],
        fingerprint: Fingerprint,
    ) -> ActionGraph:
        """Recompile via Recon+Critic with enriched context describing the failure."""
        enrichment = assemble_repair_context(failed_step, error_log, execution_history)
        return self._compile(
            fingerprint, mitm_file=self._mitm_file, proxy_url=self._proxy_url,
            repair_context=enrichment,
        )
