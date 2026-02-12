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
    model_id: str = "claude-haiku-4-5-20251001"

    # Target application
    target_url: str = "http://localhost:3000"

    # Compilation and repair
    max_critic_iterations: int = 5
    similarity_threshold: float = 0.85

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # mitmproxy
    mitm_port: int = 8080
    mitm_cert_path: str = "~/.mitmproxy/mitmproxy-ca-cert.pem"

    # Capture/Recon settings
    capture_mode: str = "file"  # "live" or "file"
    traffic_file: str = "demo/juice_shop_traffic.txt"
    recon_model_id: str = "claude-haiku-4-5-20251001"
    recon_max_iterations: int = 3

    # Logging
    log_level: str = "INFO"
