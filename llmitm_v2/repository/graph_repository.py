"""Repository pattern for Neo4j graph access."""

import json
from typing import Any, Dict, List, Optional

try:
    from neo4j import Driver, Session
except ImportError:
    # Graceful fallback when neo4j is not installed
    Driver = object  # type: ignore
    Session = object  # type: ignore

from llmitm_v2.models import ActionGraph, Finding, Fingerprint, Step


class GraphRepository:
    """Encapsulates all Neo4j operations behind semantic methods."""

    def __init__(self, driver: Driver):
        """Initialize repository with Neo4j driver singleton.

        Args:
            driver: Neo4j Driver instance
        """
        self.driver = driver

    def save_fingerprint(self, fingerprint: Fingerprint) -> None:
        """Upsert fingerprint by hash (idempotent).

        Args:
            fingerprint: Fingerprint to save
        """
        fingerprint.ensure_hash()

        def tx_func(tx: Session) -> None:
            tx.run(
                """
                MERGE (f:Fingerprint {hash: $hash})
                SET f.tech_stack = $tech_stack,
                    f.auth_model = $auth_model,
                    f.endpoint_pattern = $endpoint_pattern,
                    f.security_signals = $security_signals,
                    f.observation_text = $observation_text,
                    f.observation_embedding = $observation_embedding
                """,
                hash=fingerprint.hash,
                tech_stack=fingerprint.tech_stack,
                auth_model=fingerprint.auth_model,
                endpoint_pattern=fingerprint.endpoint_pattern,
                security_signals=fingerprint.security_signals,
                observation_text=fingerprint.observation_text,
                observation_embedding=fingerprint.observation_embedding,
            )

        with self.driver.session() as session:
            session.execute_write(tx_func)

    def get_fingerprint_by_hash(self, hash_value: str) -> Optional[Dict[str, Any]]:
        """Exact hash lookup for Fingerprint.

        Args:
            hash_value: SHA256 hash of fingerprint

        Returns:
            Fingerprint data dict or None if not found
        """

        def tx_func(tx: Session) -> Optional[Dict[str, Any]]:
            result = tx.run(
                "MATCH (f:Fingerprint {hash: $hash}) RETURN properties(f) AS fp",
                hash=hash_value,
            )
            record = result.single()
            return record["fp"] if record else None

        with self.driver.session() as session:
            return session.execute_read(tx_func)

    def find_similar_fingerprints(
        self,
        embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Vector similarity search for fingerprints.

        Args:
            embedding: Vector embedding to search for
            top_k: Number of results to return

        Returns:
            List of fingerprints with similarity scores
        """

        def tx_func(tx: Session) -> List[Dict[str, Any]]:
            result = tx.run(
                """
                CALL db.index.vector.queryNodes('fingerprintEmbeddings', $top_k, $embedding)
                YIELD node AS fp, score
                RETURN properties(fp) AS fingerprint, score
                ORDER BY score DESC
                """,
                embedding=embedding,
                top_k=top_k,
            )
            return [
                {
                    "fingerprint": record["fingerprint"],
                    "score": record["score"],
                }
                for record in result
            ]

        with self.driver.session() as session:
            return session.execute_read(tx_func)

    def save_action_graph(
        self,
        fingerprint_hash: str,
        action_graph: ActionGraph,
    ) -> None:
        """Store ActionGraph with all steps and relationships in single transaction.

        Creates: ActionGraph node, Step nodes, [:TRIGGERS], [:STARTS_WITH], [:NEXT] chain.

        Args:
            fingerprint_hash: Hash of Fingerprint to link via [:TRIGGERS]
            action_graph: ActionGraph with steps to store
        """
        action_graph.ensure_id()

        # Serialize steps with parameters as JSON strings
        steps_data = []
        for step in action_graph.steps:
            step_dict = step.model_dump()
            step_dict["parameters"] = json.dumps(step.parameters)
            steps_data.append(step_dict)

        def tx_func(tx: Session) -> None:
            # Create ActionGraph node
            tx.run(
                """
                MATCH (f:Fingerprint {hash: $fingerprint_hash})
                CREATE (ag:ActionGraph {
                    id: $ag_id,
                    vulnerability_type: $vulnerability_type,
                    description: $description,
                    confidence: $confidence,
                    times_executed: 0,
                    times_succeeded: 0,
                    created_at: datetime()
                })
                CREATE (f)-[:TRIGGERS]->(ag)
                """,
                fingerprint_hash=fingerprint_hash,
                ag_id=action_graph.id,
                vulnerability_type=action_graph.vulnerability_type,
                description=action_graph.description,
                confidence=action_graph.confidence,
            )

            # Create Step nodes
            tx.run(
                """
                MATCH (ag:ActionGraph {id: $ag_id})
                UNWIND $steps AS step_data
                CREATE (s:Step {
                    order: step_data.order,
                    phase: step_data.phase,
                    type: step_data.type,
                    command: step_data.command,
                    parameters: step_data.parameters,
                    output_file: step_data.output_file,
                    success_criteria: step_data.success_criteria,
                    deterministic: step_data.deterministic
                })
                CREATE (ag)-[:HAS_STEP]->(s)
                """,
                ag_id=action_graph.id,
                steps=steps_data,
            )

            # Create [:NEXT] chain linking steps in order
            if len(action_graph.steps) > 0:
                tx.run(
                    """
                    MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(s:Step)
                    WITH ag, s ORDER BY s.order
                    WITH ag, collect(s) AS steps
                    UNWIND range(0, size(steps) - 2) AS i
                    WITH steps[i] AS current, steps[i + 1] AS next
                    CREATE (current)-[:NEXT]->(next)
                    """,
                    ag_id=action_graph.id,
                )

                # Set [:STARTS_WITH] entry point (first step by order)
                tx.run(
                    """
                    MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(s:Step)
                    WITH ag, s ORDER BY s.order LIMIT 1
                    CREATE (ag)-[:STARTS_WITH]->(s)
                    """,
                    ag_id=action_graph.id,
                )

        with self.driver.session() as session:
            session.execute_write(tx_func)

    def get_action_graph_with_steps(
        self,
        fingerprint_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch ActionGraph with steps pre-loaded via [:NEXT] chain.

        Single query: MATCH [:TRIGGERS] → [:STARTS_WITH] → [:NEXT]*.

        Args:
            fingerprint_hash: Hash of Fingerprint to look up

        Returns:
            ActionGraph dict with populated steps list, or None
        """

        def tx_func(tx: Session) -> Optional[Dict[str, Any]]:
            result = tx.run(
                """
                MATCH (f:Fingerprint {hash: $fingerprint_hash})-[:TRIGGERS]->(ag:ActionGraph)
                MATCH (ag)-[:STARTS_WITH]->(first:Step)
                MATCH path = (first)-[:NEXT*0..100]->(s:Step)
                WITH ag, path, length(path) AS pathLen
                ORDER BY pathLen DESC
                LIMIT 1
                WITH ag, nodes(path) AS steps
                RETURN
                    properties(ag) AS graph_props,
                    [step IN steps | properties(step)] AS step_props
                """,
                fingerprint_hash=fingerprint_hash,
            )
            record = result.single()
            if not record:
                return None

            # Reconstruct ActionGraph with deserialized steps
            ag_data = dict(record["graph_props"])
            steps_data = record["step_props"]

            # Convert Neo4j DateTime objects to ISO strings
            for key in ("created_at", "updated_at"):
                if key in ag_data and hasattr(ag_data[key], "iso_format"):
                    ag_data[key] = ag_data[key].iso_format()

            # Deserialize parameters JSON
            for step_data in steps_data:
                if isinstance(step_data.get("parameters"), str):
                    step_data["parameters"] = json.loads(step_data["parameters"])

            ag_data["steps"] = steps_data
            return ag_data

        with self.driver.session() as session:
            return session.execute_read(tx_func)

    def save_finding(
        self,
        action_graph_id: str,
        finding: Finding,
    ) -> None:
        """Store Finding and link via [:PRODUCED_BY] edge.

        Args:
            action_graph_id: ID of ActionGraph that produced the finding
            finding: Finding to store
        """
        finding.ensure_id()

        def tx_func(tx: Session) -> None:
            tx.run(
                """
                MATCH (ag:ActionGraph {id: $ag_id})
                CREATE (f:Finding {
                    id: $finding_id,
                    observation: $observation,
                    severity: $severity,
                    evidence_summary: $evidence_summary,
                    target_url: $target_url,
                    observation_embedding: $observation_embedding,
                    discovered_at: datetime()
                })
                CREATE (f)-[:PRODUCED_BY]->(ag)
                """,
                ag_id=action_graph_id,
                finding_id=finding.id,
                observation=finding.observation,
                severity=finding.severity,
                evidence_summary=finding.evidence_summary,
                target_url=finding.target_url,
                observation_embedding=finding.observation_embedding,
            )

        with self.driver.session() as session:
            session.execute_write(tx_func)

    def repair_step_chain(
        self,
        action_graph_id: str,
        failed_step_order: int,
        new_steps: List[Step],
    ) -> None:
        """Replace step(s) in chain, rewire [:NEXT] edges, create [:REPAIRED_TO] edges.

        Removes the failed step and inserts new steps at its position, rewiring the chain.
        Creates [:REPAIRED_TO] relationship from old step to first new step.

        Args:
            action_graph_id: ID of ActionGraph to repair
            failed_step_order: Order number of failed step
            new_steps: Replacement steps (already ordered)
        """

        def tx_func(tx: Session) -> None:
            # Delete [:NEXT] edges into failed step
            tx.run(
                """
                MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(failed:Step {order: $failed_order})
                OPTIONAL MATCH (before:Step)-[r:NEXT]->(failed)
                DELETE r
                """,
                ag_id=action_graph_id,
                failed_order=failed_step_order,
            )
            # Delete [:NEXT] edges out of failed step, then delete it
            tx.run(
                """
                MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(failed:Step {order: $failed_order})
                OPTIONAL MATCH (failed)-[r:NEXT]->(after:Step)
                DELETE r
                DETACH DELETE failed
                """,
                ag_id=action_graph_id,
                failed_order=failed_step_order,
            )

            # Serialize new steps with JSON parameters
            new_steps_data = []
            for step in new_steps:
                step_dict = step.model_dump()
                step_dict["parameters"] = json.dumps(step.parameters)
                new_steps_data.append(step_dict)

            # Create new steps and link to ActionGraph
            tx.run(
                """
                MATCH (ag:ActionGraph {id: $ag_id})
                UNWIND $new_steps AS step_data
                CREATE (s:Step {
                    order: step_data.order,
                    phase: step_data.phase,
                    type: step_data.type,
                    command: step_data.command,
                    parameters: step_data.parameters,
                    output_file: step_data.output_file,
                    success_criteria: step_data.success_criteria,
                    deterministic: step_data.deterministic
                })
                CREATE (ag)-[:HAS_STEP]->(s)
                """,
                ag_id=action_graph_id,
                new_steps=new_steps_data,
            )

            # Rewire [:NEXT] chain around new steps
            if new_steps:
                first_new_order = new_steps[0].order
                last_new_order = new_steps[-1].order

                # Link before → first_new_step
                tx.run(
                    """
                    MATCH (ag:ActionGraph {id: $ag_id})
                    MATCH (before:Step)-[:NEXT]->(old:Step {order: $before_order})
                    WHERE NOT EXISTS {(old)-[:NEXT]->(:Step)}
                    MATCH (first:Step {order: $first_new_order})
                    CREATE (before)-[:NEXT]->(first)
                    """,
                    ag_id=action_graph_id,
                    before_order=failed_step_order - 1,
                    first_new_order=first_new_order,
                )

                # Link last_new_step → after
                tx.run(
                    """
                    MATCH (ag:ActionGraph {id: $ag_id})
                    MATCH (after:Step {order: $after_order})
                    MATCH (last:Step {order: $last_new_order})
                    CREATE (last)-[:NEXT]->(after)
                    """,
                    ag_id=action_graph_id,
                    after_order=failed_step_order + 1,
                    last_new_order=last_new_order,
                )

                # Create [:REPAIRED_TO] edge from predecessor to new step
                tx.run(
                    """
                    MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(before:Step {order: $before_order})
                    MATCH (ag)-[:HAS_STEP]->(new_step:Step {order: $first_new_order})
                    CREATE (before)-[:REPAIRED_TO {
                        reason: $reason,
                        repaired_order: $failed_order,
                        timestamp: datetime()
                    }]->(new_step)
                    """,
                    ag_id=action_graph_id,
                    before_order=failed_step_order - 1,
                    first_new_order=first_new_order,
                    failed_order=failed_step_order,
                    reason="Systemic repair",
                )

        with self.driver.session() as session:
            session.execute_write(tx_func)

    def increment_execution_count(
        self,
        action_graph_id: str,
        succeeded: bool,
    ) -> None:
        """Atomically increment execution metrics.

        Args:
            action_graph_id: ID of ActionGraph to update
            succeeded: True if execution succeeded
        """

        def tx_func(tx: Session) -> None:
            update_stmt = "SET ag.times_executed = ag.times_executed + 1"
            if succeeded:
                update_stmt += ", ag.times_succeeded = ag.times_succeeded + 1"

            tx.run(
                f"""
                MATCH (ag:ActionGraph {{id: $ag_id}})
                {update_stmt}
                """,
                ag_id=action_graph_id,
            )

        with self.driver.session() as session:
            session.execute_write(tx_func)

    def get_repair_history(
        self,
        fingerprint_hash: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Query repair history for a fingerprint's ActionGraphs.

        Fetches all [:REPAIRED_TO] relationships for ActionGraphs triggered by this fingerprint.
        Returns repair chain data for LLM to understand past repair patterns.

        Args:
            fingerprint_hash: Hash of Fingerprint to query repairs for
            max_results: Maximum number of repair records to return

        Returns:
            List of repair records with failed/repaired step info and timestamps
        """

        def tx_func(tx: Session) -> List[Dict[str, Any]]:
            result = tx.run(
                """
                MATCH (f:Fingerprint {hash: $fp_hash})-[:TRIGGERS]->(ag:ActionGraph)
                MATCH (old_step)-[:REPAIRED_TO {reason: $reason}]->(new_step)
                WHERE (ag)-[:HAS_STEP]->(old_step) OR (ag)-[:HAS_STEP]->(new_step)
                RETURN {
                    action_graph_id: ag.id,
                    old_step: properties(old_step),
                    new_step: properties(new_step),
                    repair_reason: old_step.repair_reason,
                    repair_timestamp: old_step.repair_timestamp
                } AS repair_record
                ORDER BY repair_timestamp DESC
                LIMIT $max_results
                """,
                fp_hash=fingerprint_hash,
                reason="Systemic repair",
                max_results=max_results,
            )
            return [record["repair_record"] for record in result]

        with self.driver.session() as session:
            return session.execute_read(tx_func)
