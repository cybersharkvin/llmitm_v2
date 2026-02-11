"""ActionGraph model representing compiled workflow logic."""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from llmitm_v2.models.step import Step


class ActionGraph(BaseModel):
    """Compiled workflow logic — the reusable asset that executes deterministically."""

    id: Optional[str] = Field(
        default=None,
        description="UUID. Computed, not LLM-generated."
    )
    vulnerability_type: str = Field(description="Type of vulnerability tested (e.g., 'IDOR', 'auth_bypass')")
    description: str = Field(description="Human-readable explanation of what this graph tests")
    steps: List[Step] = Field(description="Ordered CAMRO steps to execute")
    confidence: Optional[float] = Field(
        default=None,
        description="Quality score from Actor/Critic validation (0.0-1.0)"
    )
    times_executed: int = Field(default=0, description="Total execution count")
    times_succeeded: int = Field(default=0, description="Successful execution count")
    created_at: Optional[str] = Field(
        default=None,
        description="ISO8601 timestamp of compilation"
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO8601 timestamp of last modification"
    )

    def ensure_id(self) -> None:
        """Ensure ID is generated."""
        if self.id is None:
            self.id = str(uuid.uuid4())

    def success_rate(self) -> float:
        """Compute success rate as decimal (0.0-1.0).

        Returns:
            times_succeeded / times_executed if executed, else 0.0
        """
        if self.times_executed == 0:
            return 0.0
        return self.times_succeeded / self.times_executed
