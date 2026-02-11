"""Graph-oriented tools for LLM reasoning via Strands SDK.

Provides semantic access to knowledge graph for discovering similar vulnerabilities
and past repair patterns. All tools return formatted text for LLM interpretation.
"""

from typing import Any, Dict, List, Optional

try:
    from strands import tool
except ImportError:
    # Graceful fallback: define stub decorator
    def tool(func):  # type: ignore
        """Stub tool decorator when Strands is not available."""
        return func

from llmitm_v2.repository import GraphRepository


class GraphTools:
    """LLM tools for graph queries and reasoning. Use via Strands Agent."""

    def __init__(self, repo: GraphRepository, embed_model: Optional[Any] = None):
        """Initialize tools with repository and embedding model.

        Args:
            repo: GraphRepository instance for all Neo4j access
            embed_model: Sentence-transformers model (lazy-loaded if None)
        """
        self.repo = repo
        self._embed_model = embed_model

    @property
    def embed_model(self) -> Any:
        """Lazy-load embedding model on first use."""
        if self._embed_model is None:
            from sentence_transformers import SentenceTransformer

            self._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._embed_model

    @tool
    def find_similar_action_graphs(self, description: str, top_k: int = 5) -> str:
        """Find ActionGraphs for targets similar to the one described.

        Searches for similar fingerprints using embedding-based similarity,
        then retrieves associated ActionGraphs for each match.

        Args:
            description: Description of target system or vulnerability type
            top_k: Number of similar results to return (default 5)

        Returns:
            Formatted text describing similar ActionGraphs, or "No similar graphs found"
        """
        # Convert description to embedding
        embedding = self.embed_model.encode(description).tolist()

        # Find similar fingerprints
        similar_fps = self.repo.find_similar_fingerprints(embedding, top_k)
        if not similar_fps:
            return "No similar graphs found in knowledge base."

        # Fetch ActionGraphs for each similar fingerprint
        results = []
        for fp_match in similar_fps:
            fp_data = fp_match.get("fingerprint", {})
            fp_hash = fp_data.get("hash")
            score = fp_match.get("score", 0)

            if not fp_hash:
                continue

            ag_data = self.repo.get_action_graph_with_steps(fp_hash)
            if ag_data:
                results.append({
                    "similarity_score": score,
                    "fingerprint": fp_data,
                    "action_graph": ag_data,
                })

        if not results:
            return "Similar fingerprints found but no compiled ActionGraphs yet."

        # Format results for LLM
        output_lines = []
        for i, result in enumerate(results, 1):
            fp = result["fingerprint"]
            ag = result["action_graph"]
            score = result["similarity_score"]

            output_lines.append(f"\n[Similar Graph {i}] (similarity: {score:.2f})")
            output_lines.append(f"  Tech Stack: {fp.get('tech_stack', 'unknown')}")
            output_lines.append(f"  Auth Model: {fp.get('auth_model', 'unknown')}")
            output_lines.append(
                f"  Vulnerability Type: {ag.get('vulnerability_type', 'unknown')}"
            )
            output_lines.append(f"  Description: {ag.get('description', 'unknown')}")
            output_lines.append(
                f"  Success Rate: {ag.get('times_succeeded', 0)}/{ag.get('times_executed', 0)}"
            )

            steps = ag.get("steps", [])
            if steps:
                output_lines.append(f"  Steps ({len(steps)}):")
                for step in steps[:5]:  # Show first 5 steps
                    output_lines.append(
                        f"    - {step.get('phase')} ({step.get('type')}): "
                        f"{step.get('command', 'no command')}"
                    )
                if len(steps) > 5:
                    output_lines.append(f"    ... and {len(steps) - 5} more steps")

        return "\n".join(output_lines)

    @tool
    def get_repair_history(
        self,
        fingerprint_hash: str,
        max_results: int = 10,
    ) -> str:
        """Retrieve historical repair attempts for a fingerprint.

        Shows how similar systems' ActionGraphs were repaired when they failed,
        helping inform current repair strategy.

        Args:
            fingerprint_hash: Hash of the target Fingerprint
            max_results: Maximum number of repair records to return (default 10)

        Returns:
            Formatted text describing past repairs, or "No repair history found"
        """
        repairs = self.repo.get_repair_history(fingerprint_hash, max_results)

        if not repairs:
            return "No repair history found for this fingerprint."

        output_lines = ["Repair History:"]
        for i, repair in enumerate(repairs, 1):
            old_step = repair.get("old_step", {})
            new_step = repair.get("new_step", {})
            reason = repair.get("repair_reason", "unknown")

            output_lines.append(f"\n[Repair {i}]")
            output_lines.append(f"  Reason: {reason}")
            output_lines.append(
                f"  Old Step: {old_step.get('phase')} "
                f"({old_step.get('type')}) - {old_step.get('command', 'no command')}"
            )
            output_lines.append(
                f"  New Step: {new_step.get('phase')} "
                f"({new_step.get('type')}) - {new_step.get('command', 'no command')}"
            )

        return "\n".join(output_lines)
