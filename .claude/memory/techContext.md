# Technical Context

## Tech Stack

**Language**: Python 3.12+
**LLM SDK**: Strands Agents SDK (latest)
**Schema Validation**: Pydantic v2
**Graph Database**: Neo4j 5.x
**Query Language**: Cypher
**Proxy**: mitmproxy / mitmdump (latest)
**Neo4j Driver**: neo4j-python-driver v6+
**HTTP Client**: httpx (latest)
**Testing**: pytest (latest)
**Linter**: ruff (latest)
**Containerization**: Docker Compose

## Dependencies

### Core Framework
- **strands-agents** (latest): LLM orchestration. Used as **library**, not framework. `Agent` is called by our code for single-shot LLM tasks
- **strands-agents-tools** (latest): Built-in tool collection, selectively imported where needed

### Data Validation
- **pydantic** (v2): All DTOs, LLM structured output, graph serialization. Serves triple duty: validation, type safety, contracts

### Database
- **neo4j** (v6+): `Driver` singleton, per-method `Session`, managed transactions. Connection via neo4j+s:// for Aura/production

### Execution
- **mitmproxy** (latest): Traffic interception via mitmdump subprocess. Requires target to trust mitm certificate for HTTPS
- **httpx** (latest): Modern async HTTP client for direct API calls in handlers

### Development
- **pytest** (latest): Test framework for unit and integration tests
- **ruff** (latest): Linting and formatting

## Development Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Neo4j (via Docker or Aura)
- Anthropic API key

### Installation
```bash
pip install strands-agents pydantic neo4j mitmproxy httpx pytest ruff
```

### Development Server
```bash
docker-compose up  # Starts Neo4j + target app (OWASP Juice Shop)
python -m llmitm.orchestrator  # Runs orchestrator
```

### Production Build
```bash
docker build -t llmitm:latest .
docker run --env-file .env llmitm:latest
```

## Technical Constraints

### Neo4j
- **Vector dimensions**: Limited to 4096 maximum (using 384 for all-MiniLM-L6-v2)
- **HNSW index build time**: Grows with data size, requires periodic maintenance
- **Connection pool sizing**: Affects concurrent performance, default pool size = 100
- **Cypher query complexity**: Deep traversals (>5 hops) can be slow, require optimization

### Strands SDK
- **Pydantic v2 required**: Structured output validation relies on Pydantic v2 features
- **Tool serialization**: Tool functions must be serializable (no closures with external state)
- **NullConversationManager**: No memory between calls unless explicitly managed via context assembly
- **Tool call dependencies**: Sequential tool execution required to preserve dependency chains

### mitmproxy
- **Certificate trust**: Target must trust mitm certificate for HTTPS interception
- **Subprocess overhead**: Each step execution spawns subprocess, adds latency
- **Log parsing**: Depends on stable output format from mitmdump
- **Concurrency**: Single mitmdump instance per target, no parallel execution

### Python
- **Async/sync mixing**: httpx async client requires async runtime context
- **Subprocess management**: Must handle zombie processes and cleanup
- **Memory**: Large traffic logs can accumulate, require periodic cleanup

## HTTP Traffic Format

### Demo Traffic File (`demo/juice_shop_traffic.txt`)

Human-readable text format with `>>>` request and `<<<` response delimiters:

```
>>> GET /api/health HTTP/1.1
Host: localhost:3000
Authorization: Bearer token123

<<< HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json

{"status":"ok"}
```

**Structure:**
- `>>>` marks request start
- Request line: `METHOD path HTTP/VERSION`
- Headers: `Key: value` (one per line)
- Blank line before body (if present)
- Body: JSON, form data, or empty
- `<<<` marks response start
- Status line: `HTTP/VERSION code`
- Headers: same format as request
- Blank line before body
- Body: JSON, HTML, or empty

**Fingerprinter Extraction:**
- **Tech stack**: `X-Powered-By`, `Server` headers (e.g., "Express", "Apache/2.4")
- **Auth model**: `Authorization` header format ("Bearer" → JWT, "Basic" → basic auth) or presence of `Cookie`
- **Endpoint pattern**: Most common first path segment (e.g., `/api/*`, `/rest/*`)
- **Security signals**: CORS (`Access-Control-Allow-Origin: *`), CSP presence, X-Frame-Options, etc.

## Configuration

### Environment Variables

**Required**:
- `NEO4J_URI`: Neo4j connection string (e.g., `neo4j+s://your-instance.neo4j.io`)
- `NEO4J_USERNAME`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password
- `NEO4J_DATABASE`: Database name (default: `neo4j`)
- `ANTHROPIC_API_KEY`: API key for Claude via Strands SDK
- `TARGET_URL`: Base URL of target application (e.g., `http://localhost:3000`)

**Optional**:
- `MAX_CRITIC_ITERATIONS`: Maximum actor/critic loops (default: 5)
- `DEFAULT_SIMILARITY_THRESHOLD`: Fingerprint similarity cutoff (default: 0.85)
- `MITM_PORT`: mitmproxy listen port (default: 8080)
- `MITM_CERT_PATH`: Path to mitm certificate (default: `~/.mitmproxy/mitmproxy-ca-cert.pem`)
- `LOG_LEVEL`: Python logging level (default: `INFO`)
- `CAPTURE_MODE`: `file` (static traffic file) or `live` (LLM-driven recon through mitmproxy). Default: `file`
- `TRAFFIC_FILE`: Path to static traffic file (default: `demo/juice_shop_traffic.txt`). Only used when `CAPTURE_MODE=file`
- `RECON_MODEL_ID`: Model for recon agent/critic (default: `claude-haiku-4-5-20251001`). Use Opus for demo
- `RECON_MAX_ITERATIONS`: Max recon/critic loop iterations (default: 3)

### docker-compose.yml
- **neo4j service**: Neo4j 5.x with APOC and vector plugins enabled, APOC file I/O enabled, `./snapshots` bind-mounted to `/var/lib/neo4j/import/snapshots`
- **target service**: OWASP Juice Shop on port 3000
- **orchestrator service**: Python orchestrator with shared network access

### Makefile
- `make up/down` — Docker Compose lifecycle with healthcheck
- `make schema` — Run setup_schema.py with local Neo4j env vars
- `make snapshot NAME=x` — Binary dump + APOC Cypher export
- `make restore NAME=x` — Binary load + setup_schema.py
- `make reset` — Online wipe + schema recreate (no restart)
- `make test` — Run pytest

### pyproject.toml
- **Dependencies**: All pip packages with version constraints
- **Ruff config**: Line length 100, Python 3.12 target
- **Pytest config**: Test discovery patterns, coverage settings

## Strands SDK Usage

| Feature | Used? | Rationale |
|---------|-------|-----------|
| `Agent` class | **Yes** | Single-shot LLM calls with tools and structured output |
| `@tool` decorator | **Yes** | Graph-oriented reasoning tools exposed to LLM |
| `structured_output_model` | **Yes** | Pydantic schema enforcement on every LLM response |
| `SequentialToolExecutor` | **Yes** | Preserves dependency chain in tool calls |
| `BeforeToolCallEvent` hook | **Yes** | Human-in-the-loop approval for destructive actions |
| `NullConversationManager` | **Yes** | Disables conversational history; each call is fresh |
| `SlidingWindowConversationManager` | **No** | Context managed explicitly via assembly functions |
| `SessionManager` / `FileSessionManager` | **No** | Neo4j is single source of truth for all state |
| `AgentState` | **No** | State lives in graph, not SDK |
| `Swarm` / `Graph` multi-agent | **No** | Single orchestrator architecture |
| `ConcurrentToolExecutor` | **No** | Would break tool call dependency chains |

## Neo4j Capabilities Used

| Capability | Purpose | Implementation |
|------------|---------|----------------|
| **Vector Indexes** | Fuzzy fingerprint matching | `CREATE VECTOR INDEX observation_idx FOR (f:Fingerprint) ON f.observation_embedding WITH {dimension: 384, similarity_function: 'cosine'}` |
| **Cypher Queries** | All graph operations | Via GraphRepository methods |
| **Constraints** | Data integrity | `CREATE CONSTRAINT fingerprint_hash_unique FOR (f:Fingerprint) REQUIRE f.hash IS UNIQUE` |
| **Managed Transactions** | Reliability | `session.execute_read()` / `execute_write()` with auto-retry |
| **Native Vectors** | Efficient similarity search | HNSW algorithm, 384 dimensions for all-MiniLM-L6-v2 |
| **Subqueries** | Complex retrievals | `CALL`, `EXISTS`, `COUNT`, `COLLECT` subqueries for context assembly |
| **APOC** (optional) | Extended procedures | Batch operations, graph algorithms, utility functions |

## Pydantic Schemas

### Graph Node Models
```python
class Fingerprint(BaseModel):
    tech_stack: str
    auth_model: str
    endpoint_pattern: str
    security_signals: List[str]
    observation_embedding: Optional[List[float]] = None

class Step(BaseModel):
    phase: str  # CAPTURE, ANALYZE, MUTATE, REPLAY, OBSERVE
    type: str  # Handler dispatch key
    command: str
    parameters: Dict[str, str]
    output_file: Optional[str] = None
    success_criteria: Optional[str] = None  # Regex pattern
    deterministic: bool = True

class ActionGraph(BaseModel):
    id: str
    vulnerability_type: str
    description: str
    steps: List[Step]

class Finding(BaseModel):
    observation: str
    severity: str
    evidence_summary: str
```

### LLM Interaction Models
```python
class CriticFeedback(BaseModel):
    passed: bool
    feedback: str

class RepairDiagnosis(BaseModel):
    failure_type: str  # transient_recoverable, transient_unrecoverable, systemic
    suggested_fix: Optional[str] = None
```

### Context Assembly Models
```python
class CompilationContext(BaseModel):
    fingerprint: Fingerprint
    traffic_log: str
    similar_graphs: List[Dict[str, Any]] = Field(default_factory=list)

class RepairContext(BaseModel):
    failed_step: Step
    error_log: str
    graph_execution_history: List[str]
    past_repair_attempts: List[Dict[str, Any]]
```

### Execution Models
```python
class ExecutionContext(BaseModel):
    target_url: str
    session_tokens: Dict[str, str]
    previous_outputs: List[str]
    fingerprint: Fingerprint

class StepResult(BaseModel):
    stdout: str
    stderr: str
    status_code: Optional[int]
    success_criteria_matched: bool
```

## State Management

**Neo4j is the only stateful component.** There is no in-memory state, no session files, no Redis. The graph stores:

- **`(:Fingerprint)`** — target identity and characteristics
- **`(:ActionGraph)`** — compiled workflow logic (the reusable asset)
- **`(:Step)`** — individual execution steps within an ActionGraph
- **`(:Finding)`** — discovered vulnerabilities and observations
- **`[:REPAIRED_TO]`** — repair history linking old steps to new ones
- **`[:SIMILAR_TO]`** — fuzzy similarity edges between fingerprints

**The Python process is stateless.** If it crashes, the graph retains everything. The orchestrator resumes by querying the graph for the current state.

## Known Technical Issues

### Vector Index Build Time
- **Location**: Neo4j vector index creation
- **Status**: Known limitation, not blocking for hackathon scale
- **Impact**: Slow index creation with >10K fingerprints
- **Workaround**: Pre-build indexes during setup, use exact hash match for majority of queries

### Subprocess Cleanup
- **Location**: mitmdump subprocess management in StepHandler
- **Status**: Requires careful cleanup in error paths
- **Impact**: Zombie processes accumulate without proper cleanup
- **Workaround**: Use context managers and ensure `subprocess.terminate()` in finally blocks

### Async/Sync Mixing
- **Location**: httpx client in synchronous orchestrator
- **Status**: Design decision to avoid async complexity
- **Impact**: Cannot use httpx async features
- **Workaround**: Use `httpx.Client()` (sync) instead of `httpx.AsyncClient()`

## Performance Characteristics

### Cold Start (Novel Fingerprint)
- **Cost**: Expensive — full actor/critic compilation (multiple LLM calls)
- **Time**: 30-60 seconds typical (3-5 iterations before Critic approval)
- **Frequency**: One-time cost per unique target fingerprint
- **Optimization**: Cache compilation context assembly results

### Warm Start (Matched Fingerprint)
- **Cost**: Free — zero LLM calls, pure graph traversal + execution
- **Time**: 5-10 seconds for full CAMRO execution
- **Bottleneck**: mitmdump subprocess execution and HTTP request latency
- **Optimization**: Near-instant fingerprint lookup via hash index

### Self-Repair
- **Deterministic classification**: <1ms for obvious failures (timeouts, 404, 503)
- **LLM fallback**: Expensive but rare (ambiguous failures only)
- **Storage**: Repair permanently stored via `[:REPAIRED_TO]` edges for future reuse
- **Optimization**: Expand deterministic classification rules over time to reduce LLM dependency

---

**Update Frequency**: After adding dependencies or changing configuration
