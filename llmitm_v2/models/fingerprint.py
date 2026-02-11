"""Fingerprint model representing target identity and characteristics."""

import hashlib
from typing import List, Optional

from pydantic import BaseModel, Field


class Fingerprint(BaseModel):
    """Target identity and characteristics, used for matching similar targets."""

    hash: Optional[str] = Field(
        default=None,
        description="SHA256 of tech_stack|auth_model|endpoint_pattern. Computed, not LLM-generated."
    )
    tech_stack: str = Field(description="Technology stack description (e.g., 'Express.js + JWT')")
    auth_model: str = Field(description="Authentication model (e.g., 'Bearer token in Authorization header')")
    endpoint_pattern: str = Field(description="API endpoint pattern (e.g., '/api/v1/*')")
    security_signals: List[str] = Field(
        default_factory=list,
        description="Security indicators (e.g., ['CORS enabled', 'CSP present'])"
    )
    observation_text: Optional[str] = Field(
        default=None,
        description="Original text used for embedding generation"
    )
    observation_embedding: Optional[List[float]] = Field(
        default=None,
        description="Vector (1536-dim for text-embedding-3-small) for similarity search"
    )

    def compute_hash(self) -> str:
        """Compute SHA256 hash of normalized fingerprint identity.

        Returns:
            SHA256 hexdigest of 'tech_stack|auth_model|endpoint_pattern'
        """
        normalized = f"{self.tech_stack}|{self.auth_model}|{self.endpoint_pattern}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def ensure_hash(self) -> None:
        """Ensure hash is computed and stored."""
        if self.hash is None:
            self.hash = self.compute_hash()
