"""Neo4j schema setup: constraints and vector indexes."""

import logging

from neo4j import GraphDatabase

from llmitm_v2.config import Settings

logger = logging.getLogger(__name__)


def setup_schema(quiet: bool = False) -> None:
    """Create constraints and vector indexes in Neo4j.

    Idempotent — safe to run multiple times.
    """
    settings = Settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    def _print(msg: str) -> None:
        if not quiet:
            print(msg)

    try:
        with driver.session(database=settings.neo4j_database) as session:
            # Unique constraints
            _print("Creating constraints...")
            session.run(
                "CREATE CONSTRAINT fingerprint_hash_unique IF NOT EXISTS "
                "FOR (f:Fingerprint) REQUIRE f.hash IS UNIQUE"
            )
            _print("✓ Fingerprint hash unique constraint")

            session.run(
                "CREATE CONSTRAINT action_graph_id_unique IF NOT EXISTS "
                "FOR (ag:ActionGraph) REQUIRE ag.id IS UNIQUE"
            )
            _print("✓ ActionGraph id unique constraint")

            session.run(
                "CREATE CONSTRAINT finding_id_unique IF NOT EXISTS "
                "FOR (f:Finding) REQUIRE f.id IS UNIQUE"
            )
            _print("✓ Finding id unique constraint")

            # Vector indexes
            _print("\nCreating vector indexes...")
            session.run(
                """
                CREATE VECTOR INDEX fingerprintEmbeddings IF NOT EXISTS
                FOR (f:Fingerprint) ON f.observation_embedding
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }
                }
                """
            )
            _print("✓ Fingerprint embeddings vector index (384 dimensions)")

            session.run(
                """
                CREATE VECTOR INDEX findingEmbeddings IF NOT EXISTS
                FOR (f:Finding) ON f.observation_embedding
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }
                }
                """
            )
            _print("✓ Finding embeddings vector index (384 dimensions)")

            _print("\n✅ Schema setup complete")

    finally:
        driver.close()


if __name__ == "__main__":
    setup_schema()
