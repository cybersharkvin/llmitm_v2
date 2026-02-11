"""Step model representing a single CAMRO execution step."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from llmitm_v2.constants import StepPhase, StepType


class Step(BaseModel):
    """Individual execution step within an ActionGraph (CAMRO phase)."""

    model_config = ConfigDict(use_enum_values=True)

    order: int = Field(description="Execution order within the ActionGraph")
    phase: StepPhase = Field(description="CAMRO phase: CAPTURE, ANALYZE, MUTATE, REPLAY, OBSERVE")
    type: StepType = Field(description="Handler dispatch key (e.g., 'http_request', 'shell_command')")
    command: str = Field(description="Exact command to execute")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific parameters (stored as JSON in Neo4j)"
    )
    output_file: Optional[str] = Field(
        default=None,
        description="Where to store output (optional)"
    )
    success_criteria: Optional[str] = Field(
        default=None,
        description="Regex pattern for validation (optional)"
    )
    deterministic: bool = Field(
        default=True,
        description="True if no LLM reasoning required for execution"
    )
