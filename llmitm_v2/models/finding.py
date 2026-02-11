"""Finding model representing discovered vulnerabilities and observations."""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class Finding(BaseModel):
    """Discovered vulnerabilities and observations from ActionGraph executions."""

    id: Optional[str] = Field(
        default=None,
        description="UUID. Computed, not LLM-generated."
    )
    observation: str = Field(description="Vulnerability description")
    severity: str = Field(description="Severity level: critical, high, medium, low")
    evidence_summary: str = Field(description="Proof of exploitation")
    target_url: Optional[str] = Field(
        default=None,
        description="URL where vulnerability was found"
    )
    observation_embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector (384-dim for all-MiniLM-L6-v2) for similarity search"
    )
    discovered_at: Optional[str] = Field(
        default=None,
        description="ISO8601 timestamp of discovery"
    )

    def ensure_id(self) -> None:
        """Ensure ID is generated."""
        if self.id is None:
            self.id = str(uuid.uuid4())
