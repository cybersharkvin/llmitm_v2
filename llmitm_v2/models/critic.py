"""Critic models for validation and self-repair."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from llmitm_v2.constants import FailureType


class CriticFeedback(BaseModel):
    """Actor/Critic validation feedback."""

    passed: bool = Field(
        description="Whether the ActionGraph passed Critic validation"
    )
    feedback: str = Field(
        description="Detailed feedback for the Actor (used if not passed)"
    )


class RepairDiagnosis(BaseModel):
    """Self-repair failure classification and diagnosis."""

    model_config = ConfigDict(use_enum_values=True)

    failure_type: FailureType = Field(
        description="Classification: transient_recoverable, transient_unrecoverable, or systemic"
    )
    diagnosis: str = Field(
        description="What went wrong and why"
    )
    suggested_fix: Optional[str] = Field(
        default=None,
        description="Suggested repair command if systemic"
    )
