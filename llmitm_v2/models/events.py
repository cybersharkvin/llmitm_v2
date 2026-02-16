"""Pydantic models for SSE events — shared contract between backend and frontend."""

from typing import Literal

from pydantic import BaseModel

from llmitm_v2.constants import StepPhase, StepType


class StepInfo(BaseModel):
    order: int
    type: StepType
    phase: StepPhase
    command: str


class RunStartEvent(BaseModel):
    fingerprint_hash: str
    path: Literal["cold_start", "warm_start", "repair"]
    action_graph_id: str
    steps: list[StepInfo]


class StepStartEvent(BaseModel):
    order: int


class StepResultEvent(BaseModel):
    order: int
    type: StepType
    matched: bool


class CompileIterEvent(BaseModel):
    iteration: int


class ReconResultEvent(BaseModel):
    iteration: int
    plan: dict


class CriticResultEvent(BaseModel):
    iteration: int
    opportunities: int
    exploits: list[str]
    refined_plan: dict


class FailureEvent(BaseModel):
    step: int
    type: Literal["transient_recoverable", "transient_unrecoverable", "systemic"]


class RepairStartEvent(BaseModel):
    pass


class RunEndEvent(BaseModel):
    success: bool
    findings_count: int
    path: Literal["cold_start", "warm_start", "repair", "error"]
    repaired: bool
    steps_executed: int
