"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Neo4j configuration
    neo4j_uri: str
    neo4j_username: str = "neo4j"
    neo4j_password: str
    neo4j_database: str = "neo4j"

    # Anthropic API
    anthropic_api_key: str
    model_id: str = "claude-sonnet-4-5-20250929"

    # Target application
    target_url: str = "http://localhost:3000"

    # Compilation and repair
    max_critic_iterations: int = 3
    similarity_threshold: float = 0.85
    max_token_budget: int = 50_000

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # mitmproxy
    mitm_port: int = 8080
    mitm_cert_path: str = "~/.mitmproxy/mitmproxy-ca-cert.pem"

    # Capture/Recon settings
    capture_mode: str = "file"  # "live" or "file"
    traffic_file: str = "demo/juice_shop.mitm"

    # Target profile
    target_profile: str = "juice_shop"

    # Logging
    log_level: str = "INFO"
