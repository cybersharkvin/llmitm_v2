"""CLI entry point for llmitm_v2 orchestration."""

import logging
import sys
import warnings
from pathlib import Path

from neo4j import GraphDatabase

from llmitm_v2.config import Settings
from llmitm_v2.fingerprinter import Fingerprinter
from llmitm_v2.orchestrator import Orchestrator
from llmitm_v2.repository import GraphRepository
from llmitm_v2.repository.setup_schema import setup_schema

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("strands").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
logger = logging.getLogger(__name__)


def main():
    """Run orchestration command."""
    # Load settings from environment
    settings = Settings()

    # Connect to Neo4j
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    try:
        # Setup schema
        setup_schema(quiet=True)
        logger.info("Neo4j schema initialized")

        # Create repository and orchestrator
        graph_repo = GraphRepository(driver)
        orchestrator = Orchestrator(graph_repo, settings)

        if settings.capture_mode == "live":
            from llmitm_v2.capture.launcher import quick_fingerprint, run_recon

            # Fast path: deterministic fingerprint, check Neo4j for warm start
            fingerprint = quick_fingerprint(settings.target_url)
            if fingerprint:
                fingerprint.ensure_hash()
                existing_ag = graph_repo.get_action_graph_with_steps(fingerprint.hash)
                if existing_ag:
                    logger.info("Warm start: matched fingerprint %s", fingerprint.hash[:12])
                    result = orchestrator.run(fingerprint, "")
                else:
                    logger.info("Known fingerprint but no ActionGraph — running full recon")
                    recon_report = run_recon(settings)
                    # Reuse DETERMINISTIC fingerprint (not recon_report.to_fingerprint())
                    # to ensure same hash for both lookup and storage
                    result = orchestrator.run(
                        fingerprint, recon_report.traffic_log, recon_report=recon_report
                    )
            else:
                logger.info("No quick fingerprint — running full recon")
                recon_report = run_recon(settings)
                fingerprint = recon_report.to_fingerprint()
                result = orchestrator.run(
                    fingerprint, recon_report.traffic_log, recon_report=recon_report
                )
        else:
            # Static file path (unchanged)
            traffic_path = Path(__file__).parent.parent / settings.traffic_file
            if not traffic_path.exists():
                logger.error("Traffic file not found: %s", traffic_path)
                sys.exit(1)

            traffic_log = traffic_path.read_text()
            fingerprinter = Fingerprinter()
            fingerprint = fingerprinter.fingerprint(traffic_log)
            result = orchestrator.run(fingerprint, traffic_log)

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
