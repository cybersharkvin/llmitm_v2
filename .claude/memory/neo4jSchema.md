# Neo4j Schema and Architecture

## Overview

**Neo4j is the architecture, not just a database.** The graph stores the application's core logic (ActionGraph workflows), its knowledge (Fingerprints, Findings), its repair history, and its vector embeddings for semantic retrieval. All operations are fundamentally graph traversals or manipulations.

**Architecture Model:** Graph-Native Custom Logic Agent where 95% of runtime is deterministic graph traversal with zero LLM involvement.

---

## Graph Schema

### Node Types

#### (:Fingerprint)
Target identity and characteristics, used for matching similar targets.

**Properties:**
- `hash`: String (unique) — SHA256 of normalized fingerprint characteristics
- `tech_stack`: String — Technology stack description (e.g., "Express.js + JWT")
- `auth_model`: String — Authentication model (e.g., "Bearer token in Authorization header")
- `endpoint_pattern`: String — API endpoint pattern (e.g., "/api/v1/*")
- `security_signals`: List[String] — Security indicators (e.g., ["CORS enabled", "CSP present"])
- `observation_embedding`: List[Float] (384-dim) — Vector for similarity search
- `observation_text`: String — Original text used for embedding generation

**Constraints:**
```cypher
CREATE CONSTRAINT fingerprint_hash_unique IF NOT EXISTS
FOR (f:Fingerprint) REQUIRE f.hash IS UNIQUE
```

**Vector Index:**
```cypher
CREATE VECTOR INDEX fingerprintEmbeddings IF NOT EXISTS
FOR (f:Fingerprint)
ON f.observation_embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine',
    `vector.quantization.enabled`: true,
    `vector.hnsw.m`: 16,
    `vector.hnsw.ef_construction`: 100
  }
}
```

---

#### (:ActionGraph)
Compiled workflow logic — the reusable asset that executes deterministically.

**Properties:**
- `id`: String (unique) — UUID
- `vulnerability_type`: String — Type of vulnerability tested (e.g., "IDOR", "auth_bypass")
- `description`: String — Human-readable explanation
- `times_executed`: Integer — Total execution count
- `times_succeeded`: Integer — Successful execution count
- `confidence`: Float (0.0-1.0) — Quality score from Actor/Critic validation
- `created_at`: DateTime — Compilation timestamp
- `updated_at`: DateTime — Last modification timestamp

**Constraints:**
```cypher
CREATE CONSTRAINT action_graph_id_unique IF NOT EXISTS
FOR (ag:ActionGraph) REQUIRE ag.id IS UNIQUE

CREATE CONSTRAINT action_graph_key IF NOT EXISTS
FOR (ag:ActionGraph) REQUIRE (ag.fingerprint_hash, ag.vulnerability_type) IS NODE KEY
```

---

#### (:Step)
Individual execution steps within an ActionGraph (CAMRO: Capture, Analyze, Mutate, Replay, Observe).

**Properties:**
- `order`: Integer — Execution order within the ActionGraph
- `phase`: String — CAMRO phase (CAPTURE, ANALYZE, MUTATE, REPLAY, OBSERVE)
- `type`: String — Handler dispatch key (e.g., "mitmdump_command", "python_code")
- `command`: String (required) — Exact command to execute
- `parameters`: Map — Step-specific parameters as JSON
- `output_file`: String (optional) — Where to store output
- `success_criteria`: String (optional) — Regex pattern for success validation
- `deterministic`: Boolean — True if no LLM required, false if reasoning needed

**Constraints:**
```cypher
CREATE CONSTRAINT step_command_exists IF NOT EXISTS
FOR (s:Step) REQUIRE s.command IS NOT NULL

CREATE CONSTRAINT step_order_type IF NOT EXISTS
FOR (s:Step) REQUIRE s.order IS :: INTEGER
```

---

#### (:Finding)
Discovered vulnerabilities and observations from ActionGraph executions.

**Properties:**
- `id`: String (unique) — UUID
- `observation`: String — Vulnerability description
- `severity`: String — critical, high, medium, low
- `evidence_summary`: String — Proof of exploitation
- `observation_embedding`: List[Float] (384-dim) — Vector for similarity search
- `discovered_at`: DateTime — Timestamp of discovery
- `target_url`: String — URL where vulnerability was found

**Vector Index:**
```cypher
CREATE VECTOR INDEX findingEmbeddings IF NOT EXISTS
FOR (f:Finding)
ON f.observation_embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
}
```

---

### Relationship Types

#### [:TRIGGERS]
Links a Fingerprint to its ActionGraphs. This is the primary routing relationship.

```cypher
(:Fingerprint)-[:TRIGGERS]->(:ActionGraph)
```

**Properties:**
- `created_at`: DateTime — When the link was established
- `match_type`: String — "exact" or "fuzzy" (from vector search)

---

#### [:STARTS_WITH]
Entry point to the step chain within an ActionGraph.

```cypher
(:ActionGraph)-[:STARTS_WITH]->(:Step)
```

**Properties:**
- None (structural relationship only)

---

#### [:NEXT]
CAMRO chain traversal order — links steps in sequence.

```cypher
(:Step)-[:NEXT]->(:Step)
```

**Properties:**
- None (order encoded in Step.order property)

---

#### [:REPAIRED_TO]
Self-healing history — links old steps/graphs to their repaired versions.

```cypher
(:Step)-[:REPAIRED_TO {reason, timestamp, error_log}]->(:Step)
(:ActionGraph)-[:REPAIRED_TO {reason, timestamp}]->(:ActionGraph)
```

**Properties:**
- `reason`: String — Repair diagnosis (transient_recoverable, transient_unrecoverable, systemic)
- `timestamp`: DateTime — When the repair was made
- `error_log`: String — Original error that triggered repair
- `repaired_by`: String — Agent or process that performed repair

---

#### [:PRODUCED_BY]
Links findings to the ActionGraph that discovered them.

```cypher
(:Finding)-[:PRODUCED_BY]->(:ActionGraph)
```

**Properties:**
- `execution_id`: String — UUID of the specific execution that produced the finding
- `discovered_at`: DateTime — Timestamp

---

#### [:SIMILAR_TO]
Fuzzy similarity edges between fingerprints (optional optimization for caching vector search results).

```cypher
(:Fingerprint)-[:SIMILAR_TO {similarity_score}]->(:Fingerprint)
```

**Properties:**
- `similarity_score`: Float (0.0-1.0) — Cosine similarity score
- `computed_at`: DateTime — When similarity was calculated

---

## Neo4j Python Driver Patterns

### Connection Management

**Driver Singleton Pattern** — One Driver instance for the entire application:

```python
from neo4j import GraphDatabase

# Create once at startup
driver = GraphDatabase.driver(
    uri="neo4j+s://your-instance.neo4j.io",
    auth=("neo4j", "password")
)

# Verify connectivity
driver.verify_connectivity()

# Close on shutdown
driver.close()
```

**URI Schemes:**
- `neo4j+s://` — Encrypted with CA-signed certificate (Aura, production)
- `neo4j+ssc://` — Encrypted with self-signed certificate
- `neo4j://` — Unencrypted (local development only)
- `bolt+s://` — Direct encrypted connection (no routing)

---

### Transaction Patterns

**Managed Transactions (Recommended)** — Automatic retry on transient errors:

```python
def get_action_graph_by_fingerprint(tx, fingerprint_hash):
    result = tx.run(
        """
        MATCH (f:Fingerprint {hash: $hash})-[:TRIGGERS]->(ag:ActionGraph)
        RETURN ag ORDER BY ag.confidence DESC LIMIT 1
        """,
        hash=fingerprint_hash
    )
    record = result.single()
    return record["ag"] if record else None

# Execute via session
with driver.session(database="neo4j") as session:
    action_graph = session.execute_read(get_action_graph_by_fingerprint, "abc123")
```

**Per-Method Sessions** — Each GraphRepository method creates a short-lived session:

```python
class GraphRepository:
    def __init__(self, driver):
        self.driver = driver

    def get_action_graph_by_fingerprint(self, fingerprint_hash):
        with self.driver.session() as session:
            return session.execute_read(
                self._get_action_graph_tx, fingerprint_hash
            )

    @staticmethod
    def _get_action_graph_tx(tx, fingerprint_hash):
        # Transaction function must be idempotent
        result = tx.run("MATCH (f:Fingerprint {hash: $hash})...", hash=fingerprint_hash)
        return result.single()
```

---

## Vector Search Patterns

### Fuzzy Fingerprint Matching

**Pattern:** Exact match first, fall back to vector similarity if no match found.

```python
def find_or_match_fingerprint(self, fingerprint_hash, observation_embedding):
    """
    1. Try exact hash match (O(1) via unique constraint index)
    2. Fall back to vector similarity search if no exact match
    3. Return matched ActionGraphs with similarity score
    """
    query = """
    // Try exact match first
    OPTIONAL MATCH (f:Fingerprint {hash: $hash})

    // If no exact match, use vector search
    WITH f
    CALL {
        WITH f
        WHERE f IS NULL
        MATCH (fuzzy:Fingerprint)
        SEARCH fuzzy IN (
            VECTOR INDEX fingerprintEmbeddings
            FOR $embedding
            LIMIT 10
        ) SCORE AS similarity
        WHERE similarity > 0.85
        RETURN fuzzy AS matched_fp, similarity, 'fuzzy' AS match_type
        UNION
        WITH f
        WHERE f IS NOT NULL
        RETURN f AS matched_fp, 1.0 AS similarity, 'exact' AS match_type
    }

    // Get ActionGraphs for matched fingerprint
    MATCH (matched_fp)-[:TRIGGERS]->(ag:ActionGraph)
    RETURN matched_fp, ag, similarity, match_type
    ORDER BY ag.confidence DESC
    """

    with self.driver.session() as session:
        result = session.execute_read(
            lambda tx: tx.run(query, hash=fingerprint_hash, embedding=observation_embedding).data()
        )
        return result
```

---

### Context Assembly with Graph Traversal

**VectorCypherRetriever Pattern** — Vector search + graph enrichment in single query:

```python
def assemble_compilation_context(self, fingerprint, traffic_log):
    """
    Assemble context for ActionGraph compilation by:
    1. Finding similar fingerprints via vector search
    2. Traversing to their ActionGraphs
    3. Including repair history and findings
    """
    query = """
    // Find similar fingerprints
    MATCH (target:Fingerprint {hash: $fingerprint_hash})
    MATCH (similar:Fingerprint)
    SEARCH similar IN (
        VECTOR INDEX fingerprintEmbeddings
        FOR target.observation_embedding
        LIMIT 5
    ) SCORE AS similarity
    WHERE similarity > 0.80

    // Traverse to ActionGraphs with high success rates
    MATCH (similar)-[:TRIGGERS]->(ag:ActionGraph)
    WHERE ag.times_executed > 0 AND ag.times_succeeded / ag.times_executed > 0.7

    // Get steps in order
    MATCH (ag)-[:STARTS_WITH]->(first:Step)
    MATCH path = (first)-[:NEXT*0..20]->(s:Step)
    WITH ag, similarity, nodes(path) AS steps

    // Get repair history
    OPTIONAL MATCH (ag)-[:REPAIRED_TO]->(repaired:ActionGraph)

    // Get findings
    OPTIONAL MATCH (f:Finding)-[:PRODUCED_BY]->(ag)

    RETURN
        ag.id AS graph_id,
        ag.vulnerability_type AS vuln_type,
        ag.description AS description,
        similarity,
        [s IN steps | {order: s.order, phase: s.phase, command: s.command}] AS steps,
        collect(DISTINCT repaired.id) AS repair_history,
        collect(DISTINCT {severity: f.severity, observation: f.observation}) AS findings
    ORDER BY similarity DESC
    """

    with self.driver.session() as session:
        similar_graphs = session.execute_read(
            lambda tx: tx.run(query, fingerprint_hash=fingerprint.hash).data()
        )

    return CompilationContext(
        fingerprint=fingerprint,
        traffic_log=traffic_log,
        similar_graphs=similar_graphs
    )
```

---

## Neo4j GenAI Plugin Usage

### Embedding Generation

**Server-Side Batch Embedding** — Generate embeddings directly in Cypher:

```cypher
// Generate embeddings for all Fingerprints missing them
MATCH (f:Fingerprint)
WHERE f.observation_embedding IS NULL AND f.observation_text IS NOT NULL
WITH collect(f) AS fingerprints, collect(f.observation_text) AS texts
CALL ai.text.embedBatch(texts, 'OpenAI', {
  token: $openai_token,
  model: 'text-embedding-3-small'
}) YIELD index, vector
WITH fingerprints[index] AS f, vector
SET f.observation_embedding = vector
RETURN count(f) AS embeddings_generated
```

---

### LLM-Assisted Classification (Fallback)

**Deterministic-first, LLM for ambiguous cases:**

```cypher
// Use LLM to classify repair diagnosis only when deterministic check fails
MATCH (ag:ActionGraph)-[:FAILED_WITH]->(err:Error)
WHERE err.classification IS NULL
  AND err.status_code NOT IN [404, 503, 408]
  AND NOT err.message CONTAINS 'timeout'
WITH ag, err,
  ai.text.completion(
    'Classify this error as transient_recoverable, transient_unrecoverable, or systemic: ' + err.message,
    'OpenAI',
    {token: $token, model: 'gpt-4o-mini'}
  ) AS classification
SET err.classification = classification
RETURN ag.id, err.classification
```

---

## APOC Integration

### Batch Operations

**Periodic Iterate for Large Updates:**

```cypher
// Batch update step status across all ActionGraphs
CALL apoc.periodic.iterate(
  "MATCH (s:Step) WHERE s.status IS NULL RETURN s",
  "SET s.status = 'pending'",
  {batchSize: 1000, parallel: true}
) YIELD batches, total, errorMessages
RETURN batches, total, errorMessages
```

---

### Utility Functions

```cypher
// Merge ActionGraph metrics using APOC
MATCH (ag:ActionGraph {id: $graph_id})
WITH ag, apoc.map.merge(
  properties(ag),
  {times_executed: ag.times_executed + 1}
) AS updated_props
SET ag += updated_props
RETURN ag
```

---

## Query Optimization Guidelines

### Indexing Strategy

1. **Unique constraints automatically create indexes:**
   ```cypher
   CREATE CONSTRAINT FOR (f:Fingerprint) REQUIRE f.hash IS UNIQUE
   // Creates index on Fingerprint.hash
   ```

2. **Range indexes for filtering:**
   ```cypher
   CREATE INDEX action_graph_confidence IF NOT EXISTS
   FOR (ag:ActionGraph) ON (ag.confidence)
   ```

3. **Vector indexes for similarity search** (already covered above)

---

### Best Practices

| Practice | Why | Example |
|----------|-----|---------|
| **Use parameterized queries** | Enables plan caching, prevents injection | `MATCH (f:Fingerprint {hash: $hash})` not `{hash: 'abc123'}` |
| **LIMIT early** | Reduces rows processed | `MATCH (f:Fingerprint) WITH f LIMIT 10 MATCH (f)-[:TRIGGERS]->(ag)` |
| **Avoid Cartesian products** | Exponential row explosion | Always connect patterns via relationships |
| **Use EXPLAIN/PROFILE** | Understand query performance | `PROFILE MATCH (f:Fingerprint)...` |
| **Batch with UNWIND** | Single query for multiple creates | `UNWIND $steps AS step CREATE (s:Step) SET s = step` |

---

## State Management

**Neo4j is the only stateful component.** There is no in-memory state, no session files, no Redis.

**What Lives in the Graph:**
- `(:Fingerprint)` — Target identity and characteristics
- `(:ActionGraph)` — Compiled workflow logic (the reusable asset)
- `(:Step)` — Individual execution steps within an ActionGraph
- `(:Finding)` — Discovered vulnerabilities and observations
- `[:REPAIRED_TO]` — Repair history linking old steps/graphs to new ones
- `[:SIMILAR_TO]` — Fuzzy similarity edges between fingerprints

**The Python process is stateless.** If it crashes, the graph retains everything. The orchestrator resumes by querying the graph for the current state.

---

## Graph Traversal Examples

### Walk ActionGraph Step Chain

```cypher
// Get all steps for an ActionGraph in execution order
MATCH (ag:ActionGraph {id: $graph_id})-[:STARTS_WITH]->(first:Step)
MATCH path = (first)-[:NEXT*0..50]->(s:Step)
WITH nodes(path) AS steps
UNWIND steps AS step
RETURN step.order AS order, step.phase AS phase, step.command AS command
ORDER BY step.order ASC
```

---

### Find Repair Chain

```cypher
// Find the complete repair history for an ActionGraph
MATCH path = shortestPath(
  (original:ActionGraph {id: $original_id})-[:REPAIRED_TO*]-(current:ActionGraph {id: $current_id})
)
RETURN
  length(path) AS repair_count,
  [n IN nodes(path) | {id: n.id, confidence: n.confidence, created_at: n.created_at}] AS repair_chain,
  [r IN relationships(path) | {reason: r.reason, timestamp: r.timestamp}] AS repair_reasons
```

---

### Get ActionGraph Success Metrics

```cypher
// Compute success rate and related findings for ActionGraphs
MATCH (f:Fingerprint)-[:TRIGGERS]->(ag:ActionGraph)
OPTIONAL MATCH (finding:Finding)-[:PRODUCED_BY]->(ag)
WITH ag,
     CASE WHEN ag.times_executed > 0
          THEN toFloat(ag.times_succeeded) / ag.times_executed
          ELSE 0.0 END AS success_rate,
     count(DISTINCT finding) AS findings_count
RETURN
  ag.id,
  ag.vulnerability_type,
  ag.times_executed,
  success_rate,
  findings_count
ORDER BY success_rate DESC, findings_count DESC
```

---

## GraphRepository Methods

**See `strandsGuide.md` for Strands SDK integration patterns (tools, structured output, agent usage).**

### Core Query Methods

The `GraphRepository` class provides semantic methods that encapsulate Cypher queries:

```python
class GraphRepository:
    def find_similar_fingerprints(
        self,
        embedding: list[float],
        top_k: int
    ) -> list[dict]:
        """Vector similarity search for fingerprints."""
        # Implementation shown in "Vector Search Patterns" section

    def get_action_graph_by_fingerprint(
        self,
        fingerprint_hash: str
    ) -> Optional[ActionGraph]:
        """Exact hash lookup for ActionGraph."""

    def get_repairs_by_fingerprint(
        self,
        fingerprint_hash: str,
        max_results: int
    ) -> list[dict]:
        """Retrieve repair history for a fingerprint."""

    def save_action_graph(
        self,
        fingerprint: Fingerprint,
        action_graph: ActionGraph
    ) -> None:
        """Persist Pydantic model to Neo4j nodes/relationships."""
```

---

## Performance Characteristics

### Cold Start (Novel Fingerprint)
- **Vector search**: ~10-50ms for 10K fingerprints (HNSW index)
- **Graph traversal**: ~5-20ms to fetch ActionGraph + Steps chain
- **Total lookup time**: ~15-70ms before LLM compilation begins

### Warm Start (Matched Fingerprint)
- **Exact hash lookup**: <5ms (unique constraint index)
- **Fetch ActionGraph + Steps**: ~5-20ms
- **Total**: <25ms to start deterministic execution (zero LLM calls)

### Self-Repair Storage
- **Create [:REPAIRED_TO] edge**: ~5-10ms
- **Repair history traversal**: ~10-30ms (proportional to repair chain length)

---

## References

- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/current/
- Neo4j Python Driver Manual: https://neo4j.com/docs/python-manual/current/
- Neo4j Vector Indexes: https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/
- Neo4j GenAI Plugin: https://neo4j.com/docs/genai/plugin/current/
- Neo4j APOC Library: https://neo4j.com/docs/apoc/current/

---

**Update Frequency**: After schema changes, adding new node/relationship types, or discovering new Neo4j capabilities
