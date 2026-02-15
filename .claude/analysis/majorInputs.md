# Major Inputs Analysis

## Application Overview

LLMitM v2 is a **CLI-only** autonomous pentesting agent. It has no web UI, no forms, no browser interaction. All user input arrives via environment variables, command-line invocation (`python -m llmitm_v2`), and Makefile targets. Runtime data enters via HTTP responses from target applications, .mitm capture files, and LLM API responses.

---

## 1. User Input Points

### 1.1 Form Fields

**None.** This is a CLI application with no user-facing forms.

### 1.2 Selection Inputs

**None.** No dropdowns, radio buttons, or toggles.

### 1.3 File Uploads

**None.** No file upload mechanism. Files are read from local filesystem paths.

### 1.4 Action Buttons / CLI Commands

| Action | Location | Trigger | Side Effects |
|--------|----------|---------|-------------|
| Run file mode | `Makefile:40` | `make run` | Fingerprints .mitm file, compiles/executes ActionGraph, writes findings to Neo4j |
| Run live mode | `Makefile:43` | `make run-live` | Sends HTTP probes to target, runs recon agent, compiles/executes ActionGraph |
| Run NodeGoat | `Makefile:46` | `make run-nodegoat` | Same as file mode targeting NodeGoat |
| Run DVWA | `Makefile:49` | `make run-dvwa` | Same as file mode targeting DVWA |
| Setup schema | `Makefile:30` | `make schema` | Creates Neo4j constraints and vector indexes |
| Seed graph | `Makefile:52` | `make seed` | Inserts known-good IDOR ActionGraph into Neo4j |
| Break graph | `Makefile:55` | `make break-graph` | Corrupts ActionGraph steps (GET→PATCH) for repair demo |
| Fix graph | `Makefile:58` | `make fix-graph` | Reverses corruption |
| Reset DB | `Makefile:34` | `make reset` | Deletes all Neo4j nodes/relationships, recreates schema |
| Snapshot | `Makefile:25` | `make snapshot NAME=x` | Binary dump of Neo4j data to `snapshots/` |
| Restore | `Makefile:27` | `make restore NAME=x` | Loads binary dump into Neo4j |
| Run tests | `Makefile:37` | `make test` | Runs pytest suite |

### 1.5 Implicit Inputs

| Input | Source | Location | Purpose |
|-------|--------|----------|---------|
| Current working directory | OS | `__main__.py:82` | Resolves `traffic_file` path relative to project root |
| `os.environ` | OS | `shell_command_handler.py:17` | Shell steps inherit full process environment |
| System time | OS | `debug_logger.py:96` | Timestamps for debug log directories and run summaries |

---

## 2. External Data Sources

### 2.1 API Integrations

#### Service: Anthropic Messages API

| Aspect | Details |
|--------|---------|
| **Client** | `anthropic.Anthropic` (`agents.py:368,395`) |
| **Authentication** | `ANTHROPIC_API_KEY` env var |
| **Purpose** | LLM reasoning for attack plan compilation and refinement |
| **Failure Mode** | `RuntimeError` on budget exhaustion, truncated response, or missing parsed output (`agents.py:46-48,183-185`) |

**Endpoints used:**

| Endpoint | Method | Agent | Location |
|----------|--------|-------|----------|
| Messages Parse | `client.messages.parse()` | SimpleAgent (Attack Critic) | `agents.py:173` |
| Beta Messages Create | `client.beta.messages.create()` | ProgrammaticAgent (Recon) | `agents.py:296` |
| Beta Messages Parse | `client.beta.messages.parse()` | ProgrammaticAgent (Recon, structured output) | `agents.py:294` |

**Request inputs to Anthropic:**

| Field | Source | Location |
|-------|--------|----------|
| `system` prompt | Hardcoded `RECON_SYSTEM_PROMPT` or `ATTACK_CRITIC_SYSTEM_PROMPT` | `agents.py:76-159` |
| `messages` (user content) | Assembled recon/repair context | `context.py:11-101` |
| `output_format` | `AttackPlan` Pydantic model | `orchestrator.py:149,164` |
| `tools` | `code_execution` + 4 recon tool schemas | `agents.py:268-271` |
| `max_tokens` | 16384 (recon) / 4096 (critic) | `agents.py:378,396` |
| `model` | `Settings.model_id` (default `claude-sonnet-4-5-20250929`) | `config.py:23` |
| `betas` | `["code-execution-2025-08-25", "advanced-tool-use-2025-11-20"]` | `agents.py:245` |

**Response outputs consumed:**

| Field | Usage | Location |
|-------|-------|----------|
| `response.parsed_output` | Deserialized as `AttackPlan` | `agents.py:186,338-339` |
| `response.usage.input_tokens/output_tokens` | Token budget enforcement | `agents.py:35-37` |
| `response.stop_reason` | Loop control (`tool_use`, `pause_turn`, `end_turn`) | `agents.py:308-342` |
| `response.content[].type == "tool_use"` | Dispatched to recon tool handlers | `agents.py:311-329` |
| `response.container.id` | Sandbox continuity across turns | `agents.py:298-299` |

#### Service: Target Web Applications

Three target apps are attacked during execution. HTTP responses from these targets are the primary runtime input.

| Target | Default URL | Auth Mechanism | Location |
|--------|------------|----------------|----------|
| OWASP Juice Shop | `http://localhost:3000` | Bearer token (JWT) | `target_profiles.py:32-41` |
| OWASP NodeGoat | `http://localhost:4000` | Session cookie (`connect.sid`) | `target_profiles.py:42-51` |
| DVWA | `http://localhost:8081` | Session cookie (`PHPSESSID`) + CSRF token | `target_profiles.py:52-63` |

**HTTP requests sent to targets** (`http_request_handler.py:17-71`):

| Input | Source | Validation |
|-------|--------|------------|
| URL | `step.parameters["url"]` or `step.command`, resolved against `context.target_url` | Prefix check `startswith("http")` |
| Method | `step.parameters["method"]` | Default `"GET"`, uppercased |
| Headers | Merged from `step.parameters["headers"]` + `context.session_tokens` | None |
| Body | `step.parameters["body"]` — dict (form-encoded or JSON) or string | Type-checked `isinstance(body, dict)` |
| Cookies | `context.cookies` (unless `skip_cookies=True`) | None |
| Timeout | `step.parameters["timeout"]` | Default 30s |

**HTTP responses consumed from targets:**

| Field | Usage | Location |
|-------|-------|----------|
| `response.text` | Success criteria regex match, stored as `stdout` | `http_request_handler.py:58-59,65` |
| `response.status_code` | Error detection (≥400), failure classification | `http_request_handler.py:62-63` |
| `response.cookies` | Persisted to `context.cookies` for session tracking | `http_request_handler.py:42-43` |
| `response.json()` | Token extraction via `extract_token_path` | `http_request_handler.py:48-51` |
| Response headers | Fingerprint extraction (tech stack, auth model, security signals) | `fingerprinter.py:112-175` |

**Live fingerprinting probes** (`capture/launcher.py:20-56`):

| Probe | Path | Purpose |
|-------|------|---------|
| Probe 1 | `/` | Homepage headers |
| Probe 2 | `/api/` | API endpoint detection |
| Probe 3 | `/rest/` | REST endpoint detection |

### 2.2 Database: Neo4j

| Aspect | Details |
|--------|---------|
| **Type** | Graph database (Neo4j 5.x) |
| **Driver** | `neo4j.GraphDatabase.driver()` (`__main__.py:40-43`) |
| **Protocol** | `neo4j+s://` (Aura) or `bolt://` (local) |
| **Auth** | `NEO4J_USERNAME` + `NEO4J_PASSWORD` |
| **Repository** | `GraphRepository` (`repository/graph_repository.py:16`) |

**Node types (equivalent to tables):**

##### Fingerprint

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| `hash` | string | **UNIQUE** | SHA256 of tech_stack+auth_model+endpoint_pattern |
| `tech_stack` | string | — | Detected framework (e.g. "Express") |
| `auth_model` | string | — | Auth type (e.g. "Bearer", "Cookie") |
| `endpoint_pattern` | string | — | Common path prefix (e.g. "/api/*") |
| `security_signals` | string (JSON array) | — | Security header observations |
| `observation_text` | string | — | Human-readable summary |
| `observation_embedding` | float[] (384-dim) | Vector index (cosine) | For similarity search |

##### ActionGraph

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| `id` | string | **UNIQUE** | UUID |
| `vulnerability_type` | string | — | e.g. "idor_walk" |
| `description` | string | — | What this graph tests |
| `confidence` | float | 0.0-1.0 | LLM confidence score |
| `times_executed` | int | — | Execution counter |
| `times_succeeded` | int | — | Success counter |
| `created_at` | string | — | ISO8601 timestamp |
| `updated_at` | string | — | ISO8601 timestamp |

##### Step

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| `order` | int | — | Position in execution chain |
| `phase` | string | CAMRO enum | CAPTURE/ANALYZE/MUTATE/REPLAY/OBSERVE |
| `type` | string | StepType enum | HTTP_REQUEST/SHELL_COMMAND/REGEX_MATCH |
| `command` | string | — | URL path or shell command |
| `parameters` | string (JSON) | — | Handler-specific config |
| `output_file` | string | — | Optional file output path |
| `success_criteria` | string | — | Regex pattern for matching |
| `deterministic` | boolean | — | Whether step is deterministic |

##### Finding

| Property | Type | Constraints | Description |
|----------|------|-------------|-------------|
| `id` | string | **UNIQUE** | UUID |
| `observation` | string | — | What was found |
| `severity` | string | — | critical/high/medium/low |
| `evidence_summary` | string | — | Supporting evidence |
| `target_url` | string | — | Where found |
| `observation_embedding` | float[] (384-dim) | Vector index (cosine) | For similarity search |
| `discovered_at` | string | — | ISO8601 timestamp |

**Relationships:**

- `(:Fingerprint)-[:TRIGGERS]->(:ActionGraph)` — Routes fingerprints to compiled graphs
- `(:ActionGraph)-[:STARTS_WITH]->(:Step)` — Entry point for step chain
- `(:Step)-[:NEXT]->(:Step)` — CAMRO execution order
- `(:Step)-[:REPAIRED_TO]->(:Step)` — Self-healing audit trail
- `(:Finding)-[:PRODUCED_BY]->(:ActionGraph)` — Finding attribution

### 2.3 Data Files

#### .mitm Capture Files (Binary)

| Aspect | Details |
|--------|---------|
| **Format** | mitmproxy binary flow format |
| **Reader** | `mitmproxy.io.FlowReader` (`capture/launcher.py:67-68`) |
| **Default path** | `demo/juice_shop.mitm` (`config.py:43`) |
| **Purpose** | Offline fingerprinting and recon tool analysis |

**Fields extracted per flow:**

| Field | Source | Usage |
|-------|--------|-------|
| `flow.request.method` | Binary | Traffic log reconstruction |
| `flow.request.path` | Binary | Endpoint pattern extraction |
| `flow.request.headers` | Binary | Auth model detection |
| `flow.request.text` | Binary | Request body (truncated to 500 chars) |
| `flow.response.status_code` | Binary | Status line |
| `flow.response.headers` | Binary | Tech stack + security signal extraction |
| `flow.response.text` | Binary | Response body (truncated to 500 chars) |

#### Skill Guide Markdown Files (DISABLED)

| Aspect | Details |
|--------|---------|
| **Directory** | `skills/*.md` (`agents.py:63`) |
| **Loaded by** | `load_skill_guides()` (`agents.py:58`) |
| **Status** | Function exists but not called — replaced with empty string at `agents.py:370` |
| **Purpose** | Methodology coaching for recon agent (disabled for token efficiency) |

### 2.4 External Services (Docker)

| Service | Image | Port | Health Check | Purpose |
|---------|-------|------|-------------|---------|
| neo4j | `neo4j:5-community` | 7474, 7687 | `wget http://localhost:7474` | Knowledge graph |
| juiceshop | `bkimminich/juice-shop:latest` | 3000 | `wget http://localhost:3000` | Target app |
| nodegoat | `owasp-nodegoat:local` | 4000 | `wget http://localhost:4000` | Target app |
| dvwa | `vulnerables/web-dvwa:latest` | 8081 | `curl http://localhost:80` | Target app |
| mongo | `mongo:4.4` | — | None | NodeGoat backing store |
| mysql | `mysql:5.7` | — | None | DVWA backing store |
| mitmproxy | `mitmproxy/mitmproxy:latest` | 8080 | None | Reverse proxy to Juice Shop |

---

## 3. Configuration Inputs

### 3.1 Environment Variables

All loaded via `pydantic-settings` BaseSettings with `.env` file support (`config.py:9-13`).

| Variable | Default | Source | Required | Purpose | Sensitive |
|----------|---------|--------|----------|---------|-----------|
| `NEO4J_URI` | — | env/`.env` | **Yes** | Neo4j connection string | No |
| `NEO4J_USERNAME` | `"neo4j"` | env/`.env` | No | Neo4j username | No |
| `NEO4J_PASSWORD` | — | env/`.env` | **Yes** | Neo4j password | **Yes** |
| `NEO4J_DATABASE` | `"neo4j"` | env/`.env` | No | Neo4j database name | No |
| `ANTHROPIC_API_KEY` | — | env/`.env` | **Yes** | Anthropic API authentication | **Yes** |
| `MODEL_ID` | `"claude-sonnet-4-5-20250929"` | env/`.env` | No | LLM model selection | No |
| `TARGET_URL` | `"http://localhost:3000"` | env/`.env` | No | Target app base URL (overridden by profile if unset) | No |
| `MAX_CRITIC_ITERATIONS` | `3` | env/`.env` | No | Max actor/critic loop iterations | No |
| `SIMILARITY_THRESHOLD` | `0.85` | env/`.env` | No | Fingerprint similarity cutoff | No |
| `MAX_TOKEN_BUDGET` | `50000` | env/`.env` | No | Cumulative token limit per run | No |
| `EMBEDDING_MODEL` | `"all-MiniLM-L6-v2"` | env/`.env` | No | Sentence-transformers model name | No |
| `EMBEDDING_DIMENSIONS` | `384` | env/`.env` | No | Vector embedding dimensions | No |
| `MITM_PORT` | `8080` | env/`.env` | No | mitmproxy listen port | No |
| `MITM_CERT_PATH` | `"~/.mitmproxy/..."` | env/`.env` | No | Path to mitm TLS certificate | No |
| `CAPTURE_MODE` | `"file"` | env/`.env` | No | `"file"` (offline) or `"live"` (recon agent) | No |
| `TRAFFIC_FILE` | `"demo/juice_shop.mitm"` | env/`.env` | No | Path to .mitm capture file | No |
| `TARGET_PROFILE` | `"juice_shop"` | env/`.env` | No | Target profile name (`juice_shop`/`nodegoat`/`dvwa`) | No |
| `LOG_LEVEL` | `"INFO"` | env/`.env` | No | Python logging level | No |
| `DEBUG_LOGGING` | unset | env only | No | Enables per-call JSON debug logs when truthy | No |

**By Category:**
- **Secrets**: `ANTHROPIC_API_KEY`, `NEO4J_PASSWORD`
- **Connection**: `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_DATABASE`
- **Target**: `TARGET_URL`, `TARGET_PROFILE`, `CAPTURE_MODE`, `TRAFFIC_FILE`
- **LLM tuning**: `MODEL_ID`, `MAX_CRITIC_ITERATIONS`, `MAX_TOKEN_BUDGET`, `SIMILARITY_THRESHOLD`
- **Infrastructure**: `MITM_PORT`, `MITM_CERT_PATH`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`
- **Observability**: `LOG_LEVEL`, `DEBUG_LOGGING`

### 3.2 Configuration Files

| File | Format | Purpose | Hot Reload |
|------|--------|---------|------------|
| `.env` | key=value | Environment variable overrides | No |
| `docker-compose.yml` | YAML | Container orchestration | No |
| `pyproject.toml` | TOML | Package metadata, ruff/pytest config | No |

### 3.3 Hardcoded Constants

| Constant | Location | Value | Purpose | Configurable? |
|----------|----------|-------|---------|---------------|
| `MAX_CRITIC_ITERATIONS` | `constants.py:33` | `5` | **Unused** — Settings default is 3 | No (dead code) |
| `DEFAULT_SIMILARITY_THRESHOLD` | `constants.py:34` | `0.85` | **Unused** — Settings provides | No (dead code) |
| `EMBEDDING_DIMENSIONS` | `constants.py:35` | `384` | **Unused** — Settings provides | No (dead code) |
| `MITM_DEFAULT_PORT` | `constants.py:36` | `8080` | **Unused** — Settings provides | No (dead code) |
| `_MAX_BLOCK_CHARS` | `agents.py:189` | `8000` | Content block truncation limit | Possibly |
| HTTP timeout default | `http_request_handler.py:25` | `30` | Per-request timeout | No (step-level override exists) |
| Shell timeout default | `shell_command_handler.py:16` | `120` | Subprocess timeout | No (step-level override exists) |
| Quick fingerprint timeout | `capture/launcher.py:26` | `10` | httpx client timeout for probes | Possibly |
| Quick fingerprint paths | `capture/launcher.py:29` | `["/", "/api/", "/rest/"]` | Probed paths for fingerprinting | No |
| Body preview truncation | `capture/launcher.py:39,75,83` | `500` chars | Max response body for fingerprinting | No |
| Max recon iterations | `agents.py:380` | `12` | ProgrammaticAgent tool call loop cap | Possibly |
| Max critic tokens | `agents.py:396` | `4096` | SimpleAgent max_tokens | Possibly |
| Max recon tokens | `agents.py:378` | `16384` | ProgrammaticAgent max_tokens | Possibly |

### 3.4 Hardcoded Credentials

| Target | User A | User B | Location |
|--------|--------|--------|----------|
| Juice Shop | `admin@juice-sh.op` / `admin123` | `jim@juice-sh.op` / `ncc-1701` | `target_profiles.py:38-39` |
| NodeGoat | `user1` / `User1_123` | `user2` / `User2_123` | `target_profiles.py:48-49` |
| DVWA | `admin` / `password` | `gordonb` / `abc123` | `target_profiles.py:58-59` |
| Neo4j (Docker) | `neo4j` / `password` | — | `docker-compose.yml:11` |
| MySQL (Docker) | `dvwa` / `dvwa` | — | `docker-compose.yml:81-84` |

---

## 4. URL & State Inputs

### 4.1 Query Parameters

**None.** CLI application, no URL routing.

### 4.2 Route Parameters

**None.** No HTTP server or URL router.

### 4.3 Session/State Management

| Key | Type | Purpose | Persistence | Cleared On |
|-----|------|---------|-------------|------------|
| `ExecutionContext.session_tokens` | `Dict[str, str]` | Auth headers (e.g. `Authorization: Bearer ...`) | In-memory | Run completion |
| `ExecutionContext.cookies` | `Dict[str, str]` | Session cookies (e.g. `connect.sid`, `PHPSESSID`) | In-memory | Run completion |
| `ExecutionContext.previous_outputs` | `List[str]` | Stdout from each completed step | In-memory | Run completion |
| `_total_tokens` (module-level) | `int` | Cumulative token counter for budget enforcement | In-memory | Process exit |
| Neo4j graph state | Nodes + relationships | All fingerprints, action graphs, steps, findings | Neo4j database | `make reset` |

---

## 5. Internal Data Structures

### 5.1 Domain Models

**Fingerprint** (`models/fingerprint.py:9`) — Target identity derived from HTTP traffic:
```python
class Fingerprint(BaseModel):
    hash: Optional[str] = None          # SHA256 of tech_stack+auth_model+endpoint_pattern
    tech_stack: str                      # e.g. "Express"
    auth_model: str                      # e.g. "Bearer", "Cookie", "Unknown"
    endpoint_pattern: str                # e.g. "/api/*"
    security_signals: list[str] = []     # e.g. ["cors_permissive", "no_csp"]
    observation_text: str = ""           # Human-readable summary
    observation_embedding: Optional[list[float]] = None  # 384-dim vector
```
**Usage Flow**: Created by `Fingerprinter.fingerprint()` or `quick_fingerprint()` → consumed by `Orchestrator.run()` → stored in Neo4j via `GraphRepository.save_fingerprint()`.

**Step** (`models/step.py:10`) — Single CAMRO execution instruction:
```python
class Step(BaseModel):
    order: int = 0
    phase: StepPhase                     # CAPTURE|ANALYZE|MUTATE|REPLAY|OBSERVE
    type: StepType                       # HTTP_REQUEST|SHELL_COMMAND|REGEX_MATCH
    command: str                         # URL path or shell command
    parameters: dict[str, Any] = {}      # Handler-specific params
    output_file: Optional[str] = None
    success_criteria: Optional[str] = None  # Regex pattern
    deterministic: bool = True
```
**Usage Flow**: Generated by exploit step generators (`exploit_tools.py`) → stored in Neo4j → executed by handlers during graph traversal.

**AttackPlan** (`models/recon.py:44`) — LLM-generated attack prescription:
```python
class AttackPlan(BaseModel):
    attack_plan: list[AttackOpportunity] = []

class AttackOpportunity(BaseModel):
    opportunity: str                     # What the attack tests
    recon_tool_used: ReconTool           # Which tool found evidence
    observation: str                     # Specific evidence from tool
    suspected_gap: str                   # Business intent vs code gap
    recommended_exploit: ExploitTool     # Which exploit to run
    exploit_target: str                  # Concrete URL path (auto-sanitized)
    exploit_reasoning: str               # Why this exploit fits
```
**Usage Flow**: Produced by Recon Agent → refined by Attack Critic → converted to ActionGraph by `attack_plan_to_action_graph()`.

### 5.2 Step Parameters (Handler-Specific)

The `step.parameters` dict is the primary data contract between compilation and execution. Each handler reads specific keys:

**HTTPRequestHandler parameters:**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `url` / `path` | str | `step.command` | Request URL (resolved against target_url) |
| `method` | str | `"GET"` | HTTP method |
| `headers` | dict | `{}` | Extra request headers |
| `body` | dict/str | None | Request body (form-encoded by default) |
| `json` | bool | False | Send body as JSON instead of form-encoded |
| `timeout` | int | 30 | Per-request timeout in seconds |
| `skip_cookies` | bool | False | Omit context cookies from request |
| `extract_token_path` | str | None | Dotted path into JSON response for token extraction (e.g. `"authentication.token"`) |

**ShellCommandHandler parameters:**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `timeout` | int | 120 | Subprocess timeout in seconds |
| `env` | dict | `{}` | Extra environment variables (merged with `os.environ`) |
| `cwd` | str | None | Working directory for subprocess |

**RegexMatchHandler parameters:**

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `source` | str/int | `"last"` | Which previous output to match against (index or `"last"`) |
| `group` | int | 0 | Capture group to extract (0 = full match) |

### 5.3 Interpolation Tokens

Step parameters support `{{previous_outputs[N]}}` tokens resolved at execution time (`orchestrator.py:308-327`):

| Token | Resolves To | Example |
|-------|-------------|---------|
| `{{previous_outputs[0]}}` | `context.previous_outputs[0]` | Login response body |
| `{{previous_outputs[-1]}}` | Last output | Most recent step's stdout |
| `{{previous_outputs[N]}}` | Nth output | Specific step result |

---

## 6. Specialized Inputs

### 6.1 HTTP Traffic (Fingerprinter Input)

The `Fingerprinter` class (`fingerprinter.py:9`) parses a text-based traffic log format:

```
>>> GET /api/Users HTTP/1.1
Host: localhost:3000
Authorization: Bearer eyJhbGc...

<<< HTTP/1.1 200 OK
X-Powered-By: Express
Content-Type: application/json

{"id":1,"email":"admin@juice-sh.op"}
```

**Extraction rules** (all deterministic, no ML):

| Signal | Header/Pattern | Extracted Value | Location |
|--------|---------------|-----------------|----------|
| Tech stack | `X-Powered-By` or `Server` | First match (e.g. "Express") | `fingerprinter.py:112-121` |
| Auth model | `Authorization: Bearer` | `"Bearer"` | `fingerprinter.py:123-140` |
| Auth model | `Authorization: Basic` | `"Basic"` | `fingerprinter.py:123-140` |
| Auth model | `Cookie:` header present | `"Cookie"` | `fingerprinter.py:123-140` |
| Endpoint pattern | Most common first path segment | e.g. `"/api/*"` | `fingerprinter.py:142-158` |
| CORS permissive | `Access-Control-Allow-Origin: *` | `"cors_permissive"` | `fingerprinter.py:160-175` |
| No CSP | Missing `Content-Security-Policy` | `"no_csp"` | `fingerprinter.py:160-175` |
| Clickjack protected | `X-Frame-Options` present | `"clickjacking_protected"` | `fingerprinter.py:160-175` |

### 6.2 Recon Tool Outputs (LLM Sandbox Input)

Four recon tools return JSON strings consumed by the LLM inside its code_execution sandbox:

| Tool | Input | Output | Location |
|------|-------|--------|----------|
| `response_inspect` | `mitm_file`, optional `endpoint_filter` regex | Flow summaries or filtered details | `recon_tools.py:102-141` |
| `jwt_decode` | `mitm_file`, optional `token_header` | Decoded JWT header + claims | `recon_tools.py:143-204` |
| `header_audit` | `mitm_file` | Missing security headers, CORS issues, server info leaks | `recon_tools.py:206-269` |
| `response_diff` | `mitm_file`, `flow_index_a`, `flow_index_b` | Structural diff of two responses | `recon_tools.py:271-316` |

---

## Summary

### Input Counts

| Category | Count | Critical |
|----------|-------|----------|
| Environment variables | 19 | `ANTHROPIC_API_KEY`, `NEO4J_PASSWORD` |
| Hardcoded credentials | 5 sets | All target app + Docker service credentials |
| External APIs | 1 (Anthropic) | Token budget enforcement |
| Database connections | 1 (Neo4j) | All persistent state |
| Target applications | 3 | HTTP responses are primary runtime input |
| File inputs | 2 types (.mitm, skill guides) | .mitm is primary offline input |
| CLI actions | 12 Makefile targets | `make reset` is destructive |
| Internal data models | 8 Pydantic models | Step parameters are the key data contract |
| **TOTAL** | ~50 distinct inputs | |

### Data Flow

```
Environment Variables ──→ Settings ──→ Orchestrator
                                           │
.mitm File ──→ FlowReader ──→ Fingerprinter ──→ Fingerprint
                    │                                │
                    ▼                                ▼
              Recon Tools ──→ LLM (Anthropic) ──→ AttackPlan
                                                     │
                                                     ▼
              Exploit Tools ──→ ActionGraph ──→ Neo4j (persist)
                                    │
                                    ▼
              Step Handlers ──→ HTTP to Target ──→ Response
                                                     │
                                                     ▼
                                              StepResult ──→ Finding ──→ Neo4j
```

### Security Considerations

| Input | Risk | Mitigation | Status |
|-------|------|-----------|--------|
| Shell commands in Steps | Command injection | Steps are LLM-generated, not user-supplied; `deterministic` flag | Partial — no sanitization of `step.command` |
| HTTP request URLs | SSRF | Target URL constrained by profile `default_url` | Partial — LLM can specify arbitrary paths |
| `extract_token_path` | Object traversal | Splits on `.` and indexes into response JSON | Implemented — wraps in try/except |
| `.mitm` file path | Path traversal | Resolved relative to project root | Partial — no path validation |
| Neo4j credentials | Credential exposure | Loaded from env vars, not committed | Implemented |
| Anthropic API key | Credential exposure | Loaded from env vars | Implemented |
| Target app credentials | Credential exposure | **Hardcoded in source** (`target_profiles.py`) | Gap — should move to env vars |
| Docker credentials | Credential exposure | **Hardcoded in docker-compose.yml** | Gap — should move to `.env` template |
| LLM output (AttackPlan) | Prompt injection / hallucination | Grammar-constrained decoding + Pydantic validation + `exploit_target` validator | Implemented |
| Token budget | Cost runaway | Cumulative counter with configurable limit | Implemented |
| Response body size | Memory exhaustion | Body truncated to 500 chars for fingerprinting; `_MAX_BLOCK_CHARS=8000` for LLM context | Implemented |

### Validation Strategy

1. **Boundary validation**: Pydantic models validate all LLM outputs via grammar-constrained decoding. Environment variables validated by pydantic-settings on startup. `ReconTool`/`ExploitTool` Literal types prevent hallucinated tool names.
2. **Type coercion**: `AttackOpportunity.exploit_target` field_validator auto-fixes `{id}` → `1` and strips full URLs to paths (`models/recon.py:34`). `StepPhase`/`StepType`/`FailureType` enums enforce valid string values.
3. **Sanitization**: `_sanitize_content()` truncates oversized LLM response blocks (`agents.py:205`). `_truncate_dict()` caps string values at 8000 chars (`agents.py:192`).
4. **Error handling**: HTTP errors produce `StepResult(stderr=...)` rather than exceptions (`http_request_handler.py:70-71`). Shell timeouts caught and reported (`shell_command_handler.py:38-39`). Token budget exhaustion raises `RuntimeError` (`agents.py:46-48`).

### Known Gaps

- [ ] Target app credentials hardcoded in `target_profiles.py` — should be env var backed
- [ ] Docker service credentials hardcoded in `docker-compose.yml` — should use `.env` template
- [ ] `step.command` passed directly to `subprocess.run(shell=True)` — no sanitization (mitigated by steps being internally generated, not user-supplied)
- [ ] `.mitm` file path not validated against directory traversal
- [ ] `quick_fingerprint()` uses `verify=False` for TLS — acceptable for local testing but insecure in production
- [ ] No rate limiting on HTTP requests to target applications
- [ ] 4 unused constants in `constants.py` (`MAX_CRITIC_ITERATIONS`, `DEFAULT_SIMILARITY_THRESHOLD`, `EMBEDDING_DIMENSIONS`, `MITM_DEFAULT_PORT`)
