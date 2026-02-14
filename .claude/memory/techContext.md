# Technical Context

## Tech Stack

**Language**: Python 3.12+
**LLM SDK**: Anthropic Python SDK (v0.79.0+) — native structured output via grammar-constrained decoding
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
- **anthropic** (v0.79.0+): Native Anthropic SDK. `client.messages.parse(output_format=Model)` for structured output (grammar-constrained decoding, 1 API call). `client.beta.messages.tool_runner(tools, output_format=Model)` for tool-using agents. `@beta_tool` decorator for tool definitions.

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
pip install anthropic pydantic neo4j mitmproxy httpx pytest ruff
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

### Anthropic SDK
- **Pydantic v2 required**: `output_format=` param validates against Pydantic v2 models
- **`@beta_tool` on closures**: Works on standalone functions; class methods need closure wrappers (see `create_recon_tools()`, `create_graph_tools()`)
- **`tool_runner` is beta**: API may change; fallback is manual 20-line while loop
- **Grammar compilation latency**: First call per schema has extra latency (~1-2s), cached 24h server-side
- **No conversation memory**: Each `messages.parse()` / `tool_runner()` call is stateless; context managed via assembly functions
- **`max_iterations` on ProgrammaticAgent**: Caps tool call loop. Set to 8 for recon agent to prevent context bloat

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
- `ANTHROPIC_API_KEY`: API key for Claude via Anthropic SDK
- `TARGET_URL`: Base URL of target application (e.g., `http://localhost:3000`)

**Optional**:
- `MAX_CRITIC_ITERATIONS`: Maximum actor/critic loops (default: 3)
- `MAX_TOKEN_BUDGET`: Cumulative token limit across all API calls in one run (default: 150000). Raises RuntimeError if exceeded
- `DEFAULT_SIMILARITY_THRESHOLD`: Fingerprint similarity cutoff (default: 0.85)
- `MITM_PORT`: mitmproxy listen port (default: 8080)
- `MITM_CERT_PATH`: Path to mitm certificate (default: `~/.mitmproxy/mitmproxy-ca-cert.pem`)
- `LOG_LEVEL`: Python logging level (default: `INFO`)
- `TARGET_PROFILE`: Target profile name (`juice_shop`, `nodegoat`, `dvwa`). Default: `juice_shop`
- `CAPTURE_MODE`: `file` (static traffic file) or `live` (LLM-driven recon through mitmproxy). Default: `file`
- `TRAFFIC_FILE`: Path to .mitm capture file (default: `demo/juice_shop.mitm`). Only used when `CAPTURE_MODE=file`

### docker-compose.yml
- **neo4j service**: Neo4j 5.x with APOC and vector plugins enabled, APOC file I/O enabled, `./snapshots` bind-mounted to `/var/lib/neo4j/import/snapshots`
- **juiceshop service**: OWASP Juice Shop on port 3000
- **nodegoat service**: OWASP NodeGoat on port 4000 (built from source as `owasp-nodegoat:local`, requires `command: node server.js` and `docker exec llmitm_nodegoat node artifacts/db-reset.js` on first run)
- **dvwa service**: DVWA on port 8081 (requires DB setup via `/setup.php` on first run)
- **mongo service**: MongoDB 4.4 for NodeGoat
- **mysql service**: MySQL 5.7 for DVWA
- **mitmproxy service**: Reverse proxy to Juice Shop on port 8080

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

## Anthropic SDK Usage

| Feature | Used? | Rationale |
|---------|-------|-----------|
| `client.messages.parse()` | **Yes** | Single-shot structured output via grammar-constrained decoding. Used by SimpleAgent for Attack Critic |
| `client.beta.messages.create()` | **Yes** | Programmatic tool calling with code_execution sandbox + custom tools. Used by ProgrammaticAgent for Recon Agent |
| `code_execution_20250825` tool | **Yes** | Agent writes Python in sandbox, calls `await mitmdump(...)`. Intermediate results stay in sandbox |
| `allowed_callers` on custom tools | **Yes** | mitmdump tool callable only from code_execution sandbox, not directly by Claude |
| Beta headers | **Yes** | `code-execution-2025-08-25` + `advanced-tool-use-2025-11-20` required for ProgrammaticAgent |
| `output_format=PydanticModel` | **Yes** | Grammar-constrained decoding ensures valid JSON matching Pydantic schema |
| `response.parsed_output` | **Yes** | Pre-validated Pydantic instance from structured output response |
| `response.usage` | **Yes** | Logged after every API call. Cumulative counter enforces 50K token budget |
| `@beta_tool` decorator | **Partial** | Still used in `graph_tools.py` for embedding-based queries. Not used by main agent pipeline |

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

### Cold Start (Novel Fingerprint) — VERIFIED
- **Cost**: 7 API calls, ~37K tokens (Sonnet 4.5)
- **Time**: ~80 seconds (recon agent + critic + 5-step execution)
- **Frequency**: One-time cost per unique target fingerprint
- **Optimization**: 1 exploit per graph, max_iterations=8, no skill guides

### Warm Start (Matched Fingerprint) — VERIFIED
- **Cost**: Zero — 0 API calls, 0 tokens
- **Time**: ~2 seconds (fingerprint hash lookup + 5-step HTTP execution)
- **Bottleneck**: HTTP request latency to target
- **Optimization**: Near-instant fingerprint lookup via hash index

### Self-Repair — VERIFIED
- **Cost**: 9 API calls, ~56K tokens (recon agent recompiles)
- **Time**: ~90 seconds (3 failed steps + recompile + 5 clean steps)
- **Guard**: Max 1 repair per execution run (prevents runaway recompilation)
- **Storage**: New ActionGraph stored with newer created_at; ORDER BY DESC selects it on next warm start

---

**Update Frequency**: After adding dependencies or changing configuration
