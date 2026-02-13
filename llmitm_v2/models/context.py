"""Context models for different execution phases."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from llmitm_v2.models.fingerprint import Fingerprint


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
    cookies: Dict[str, str] = Field(
        default_factory=dict,
        description="HTTP cookies accumulated during execution (Set-Cookie extraction)"
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


class ExecutionResult(BaseModel):
    """Result of a full ActionGraph execution."""

    success: bool = Field(description="Whether execution completed successfully")
    findings: List[Any] = Field(default_factory=list, description="Findings discovered during execution")
    steps_executed: int = Field(default=0, description="Number of steps executed")
    error_log: Optional[str] = Field(default=None, description="Error details if execution failed")
    repaired: bool = Field(default=False, description="Whether ActionGraph was repaired during execution")


class OrchestratorResult(BaseModel):
    """Result of a full orchestrator run (cold/warm start + execution)."""

    path: str = Field(description="Execution path: 'cold_start' or 'warm_start'")
    action_graph_id: Optional[str] = Field(default=None, description="ID of ActionGraph used")
    execution: Optional[ExecutionResult] = Field(default=None, description="Execution result")
    compiled: bool = Field(default=False, description="Whether ActionGraph was compiled this run")
    repaired: bool = Field(default=False, description="Whether ActionGraph was repaired this run")
