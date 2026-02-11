"""Neo4j schema setup: constraints and vector indexes."""

from neo4j import GraphDatabase

from llmitm_v2.config import Settings


def setup_schema() -> None:
    """Create constraints and vector indexes in Neo4j.

    Idempotent — safe to run multiple times.
    """
    settings = Settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    try:
        with driver.session(database=settings.neo4j_database) as session:
            # Unique constraints
            print("Creating constraints...")
            session.run(
                "CREATE CONSTRAINT fingerprint_hash_unique IF NOT EXISTS "
                "FOR (f:Fingerprint) REQUIRE f.hash IS UNIQUE"
            )
            print("✓ Fingerprint hash unique constraint")

            session.run(
                "CREATE CONSTRAINT action_graph_id_unique IF NOT EXISTS "
                "FOR (ag:ActionGraph) REQUIRE ag.id IS UNIQUE"
            )
            print("✓ ActionGraph id unique constraint")

            session.run(
                "CREATE CONSTRAINT finding_id_unique IF NOT EXISTS "
                "FOR (f:Finding) REQUIRE f.id IS UNIQUE"
            )
            print("✓ Finding id unique constraint")

            # Vector indexes
            print("\nCreating vector indexes...")
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
            print("✓ Fingerprint embeddings vector index (384 dimensions)")

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
            print("✓ Finding embeddings vector index (384 dimensions)")

            print("\n✅ Schema setup complete")

    finally:
        driver.close()


if __name__ == "__main__":
    setup_schema()
