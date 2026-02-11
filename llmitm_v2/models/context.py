"""Context models for different execution phases."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from llmitm_v2.models.fingerprint import Fingerprint
from llmitm_v2.models.step import Step


class ExecutionContext(BaseModel):
    """Runtime context during ActionGraph execution."""

    target_url: str = Field(description="Base URL of target application")
    session_tokens: Dict[str, str] = Field(
        default_factory=dict,
        description="Authentication tokens accumulated during execution"
    )
    previous_outputs: List[str] = Field(
        default_factory=list,
        description="Output from previous steps (threaded through execution)"
    )
    fingerprint: Fingerprint = Field(
        description="Target fingerprint for execution context"
    )


class StepResult(BaseModel):
    """Result of a single step execution."""

    stdout: str = Field(
        default="",
        description="Standard output from step execution"
    )
    stderr: str = Field(
        default="",
        description="Standard error from step execution"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="HTTP status code (if applicable)"
    )
    success_criteria_matched: bool = Field(
        default=False,
        description="Whether output matched success_criteria regex"
    )


class CompilationContext(BaseModel):
    """Context for ActionGraph compilation (Actor/Critic phase)."""

    fingerprint: Fingerprint = Field(
        description="Target fingerprint driving compilation"
    )
    traffic_log: str = Field(
        description="Sample HTTP traffic from target"
    )
    similar_graphs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Similar ActionGraphs from vector search (for reference)"
    )


class RepairContext(BaseModel):
    """Context for self-repair phase (LLM diagnosis and fix)."""

    failed_step: Step = Field(
        description="The step that failed"
    )
    error_log: str = Field(
        description="Error message/log from step execution"
    )
    graph_execution_history: List[str] = Field(
        default_factory=list,
        description="Previous steps in execution order"
    )
    past_repair_attempts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Historical repair records for similar errors"
    )
