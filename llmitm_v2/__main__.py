"""CLI entry point for llmitm_v2 orchestration."""

import logging
import sys
from pathlib import Path

from neo4j import GraphDatabase

from llmitm_v2.config import Settings
from llmitm_v2.orchestrator import Orchestrator
from llmitm_v2.repository import GraphRepository
from llmitm_v2.repository.setup_schema import setup_schema

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main():
    """Run orchestration command."""
    settings = Settings()

    # Wire token budget from settings
    from llmitm_v2.orchestrator.agents import set_token_budget
    set_token_budget(settings.max_token_budget)

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    try:
        setup_schema(quiet=True)
        logger.info("Neo4j schema initialized")

        graph_repo = GraphRepository(driver)
        orchestrator = Orchestrator(graph_repo, settings)

        if settings.capture_mode == "live":
            from llmitm_v2.capture.launcher import quick_fingerprint

            # Fast path: deterministic fingerprint, check Neo4j for warm start
            fingerprint = quick_fingerprint(settings.target_url)
            proxy_url = f"http://127.0.0.1:{settings.mitm_port}"

            if fingerprint:
                fingerprint.ensure_hash()
                existing_ag = graph_repo.get_action_graph_with_steps(fingerprint.hash)
                if existing_ag:
                    logger.info("Warm start: matched fingerprint %s", fingerprint.hash[:12])
                    result = orchestrator.run(fingerprint)
                else:
                    logger.info("Known fingerprint but no ActionGraph — running recon")
                    result = orchestrator.run(fingerprint, proxy_url=proxy_url)
            else:
                logger.info("No quick fingerprint — running recon against live target")
                # Create minimal fingerprint from target URL
                from llmitm_v2.models import Fingerprint
                fingerprint = Fingerprint(
                    tech_stack="Unknown",
                    auth_model="Unknown",
                    endpoint_pattern="/",
                    security_signals=[],
                )
                result = orchestrator.run(fingerprint, proxy_url=proxy_url)
        else:
            # File mode: .mitm binary capture
            traffic_path = Path(__file__).parent.parent / settings.traffic_file
            if not traffic_path.exists():
                logger.error("Traffic file not found: %s", traffic_path)
                sys.exit(1)

            # Extract fingerprint from .mitm file (no live target needed)
            from llmitm_v2.capture.launcher import fingerprint_from_mitm
            fingerprint = fingerprint_from_mitm(str(traffic_path))
            if fingerprint is None:
                from llmitm_v2.models import Fingerprint
                fingerprint = Fingerprint(
                    tech_stack="Unknown",
                    auth_model="Unknown",
                    endpoint_pattern="/",
                    security_signals=[],
                )

            result = orchestrator.run(
                fingerprint, mitm_file=str(traffic_path)
            )

        logger.info(
            "Fingerprint: tech_stack=%s, auth_model=%s, endpoint_pattern=%s",
            fingerprint.tech_stack,
            fingerprint.auth_model,
            fingerprint.endpoint_pattern,
        )

        # Print results
        logger.info("Orchestration complete")
        logger.info("Path: %s", result.path)
        logger.info("Compiled: %s", result.compiled)
        logger.info("Repaired: %s", result.repaired)
        if result.execution:
            logger.info("Success: %s", result.execution.success)
            logger.info("Steps executed: %d", result.execution.steps_executed)
            logger.info("Findings: %d", len(result.execution.findings))

    finally:
        driver.close()


if __name__ == "__main__":
    main()
