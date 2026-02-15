# Data Flows Analysis

## 1. State Management

### 1.1 State Containers

| State | Location | Type | Scope | Persistence |
|-------|----------|------|-------|-------------|
| Neo4j Graph | `repository/graph_repository.py:16` | Neo4j Driver + Cypher | Global | Database (disk) |
| ExecutionContext | `models/context.py:11` | Pydantic BaseModel (target_url, session_tokens, previous_outputs, cookies, fingerprint) | Per-execution | Memory (ephemeral) |
| Settings | `config.py:6` | Pydantic BaseSettings (neo4j, anthropic, target, compilation, embedding config) | Global | Environment vars |
| TargetProfile registry | `target_profiles.py:67` | Dict[str, TargetProfile] — 3 profiles: juice_shop, nodegoat, dvwa | Global | Memory (static) |
| Token budget counter | `orchestrator/agents.py:26` | Module-level `_total_tokens: int`, `_max_token_budget: int` | Global | Memory (per-process) |
| Debug log accumulator | `debug_logger.py:96` | Module-level `_calls: list`, `_events: list`, `_run_dir: Path` | Global | Memory → disk at end |

### 1.2 State Updates

| State | Updated By | Trigger | Side Effects |
|-------|------------|---------|--------------|
| ExecutionContext.previous_outputs | `_execute()` loop (`orchestrator.py:191`) | Step execution succeeds | Available for `{{previous_outputs[N]}}` interpolation in subsequent steps |
| ExecutionContext.session_tokens | HTTPRequestHandler (`http_request_handler.py:17`) | `extract_token_path` param in step | Merged into headers of all subsequent HTTP steps |
| ExecutionContext.cookies | HTTPRequestHandler | HTTP response has Set-Cookie | Sent with all subsequent HTTP steps (unless `skip_cookies=True`) |
| _total_tokens | `_check_and_log_usage()` (`agents.py:32`) | Every Anthropic API call | Raises RuntimeError if budget exceeded |
| Neo4j (:Fingerprint) | `save_fingerprint()` (`graph_repository.py:27`) | `orchestrator.run()` entry | Idempotent MERGE upsert by hash |
| Neo4j (:ActionGraph) | `save_action_graph()` (`graph_repository.py:116`) | After compilation | CREATE node + step chain + [:TRIGGERS] edge |
| Neo4j (:Finding) | `save_finding()` (`graph_repository.py:265`) | OBSERVE step matches criteria | CREATE node + [:PRODUCED_BY] edge |
| Neo4j execution counters | `increment_execution_count()` (`graph_repository.py:423`) | After execution completes | times_executed++ and optionally times_succeeded++ |

**State Summary**: Neo4j is the only persistent state store. All execution state (tokens, cookies, outputs) is ephemeral per-run. Module-level globals track token budget and debug logs within a single process lifetime.

---

## 2. Component Communication

### 2.1 Data Passing

| From | To | Mechanism | Data |
|------|----|-----------|------|
| `__main__.main()` | `Orchestrator.__init__()` | Constructor DI | GraphRepository, Settings |
| `Orchestrator.run()` | `_try_warm_start()` | Method call | Fingerprint (with hash computed) |
| `Orchestrator.run()` | `_compile()` | Method call | Fingerprint, mitm_file or proxy_url |
| `Orchestrator.run()` | `_execute()` | Method call | ActionGraph, Fingerprint |
| `_compile()` | `create_recon_agent()` (`agents.py:347`) | Factory call | mitm_context string, model_id, api_key |
| `_compile()` | `create_attack_critic()` (`agents.py:384`) | Factory call | model_id, api_key |
| `_compile()` | `attack_plan_to_action_graph()` (`orchestrator.py:43`) | Function call | AttackPlan (Pydantic), TargetProfile |
| `attack_plan_to_action_graph()` | Exploit step generators | Dict dispatch via `EXPLOIT_STEP_GENERATORS` | exploit_target str, observation str, TargetProfile |
| `_execute()` | `get_handler()` (`handlers/registry.py:18`) | Registry lookup | StepType enum → handler instance |
| `_execute()` | `handler.execute()` | Method call | Step (interpolated), ExecutionContext |
| ProgrammaticAgent | Recon tool handlers | Dict dispatch via `TOOL_HANDLERS` | Tool args (mitm_file, filters, indices) |
| `_handle_step_failure()` | `classify_failure()` (`failure_classifier.py:6`) | Function call | error_log str, status_code int |
| `_handle_step_failure()` | `_repair()` (`orchestrator.py:330`) | Method call | ActionGraph, failed Step, error_log, execution_history |

### 2.2 Event/Callback Flow

| Event | Source | Handler | Effect |
|-------|--------|---------|--------|
| API response received | Anthropic SDK | `_check_and_log_usage()` (`agents.py:32`) | Increments token counter; optionally writes debug JSON |
| Step execution fails | `_execute()` loop | `_handle_step_failure()` (`orchestrator.py:267`) | Classifies → retry / abort / repair |
| OBSERVE step matches | `_execute()` loop | Finding creation block in `_execute()` | Creates Finding, saves to Neo4j |
| Budget exceeded | `_check_budget()` (`agents.py:44`) | RuntimeError raised | Aborts entire run |
| mitmproxy response | mitmdump runtime | `LLMitMCaptureAddon.response()` (`capture/addon.py:18`) | Appends flow dict to capture list |

### 2.3 Shared State Access

| State | Consumers | Access Pattern |
|-------|-----------|----------------|
| Neo4j graph | `_try_warm_start`, `save_fingerprint`, `save_action_graph`, `save_finding`, `increment_execution_count`, `get_action_graph_with_steps`, `find_similar_fingerprints`, `get_repair_history` | Read-write via GraphRepository singleton |
| ExecutionContext | All step handlers + `_interpolate_params` (read); HTTPRequestHandler (write cookies/tokens); `_execute` loop (write previous_outputs) | Read-write, single-threaded |
| _total_tokens | `_check_budget` (read) + `_check_and_log_usage` (write) | Read-write, module-level global |

---

## 3. Data Transformations

### 3.1 Validation

| Input | Validator | Location | Rules | On Failure |
|-------|-----------|----------|-------|------------|
| LLM output → AttackPlan | Pydantic + grammar-constrained decoding | `agents.py:171` | Fields match schema; ReconTool/ExploitTool are valid Literals | API returns validation error; agent retries |
| exploit_target field | `must_be_concrete_path` validator | `models/recon.py:34` | Strips `{id}` templates → `1`; strips full URLs to path-only | Auto-corrected silently |
| Fingerprint identity | `compute_hash()` | `models/fingerprint.py:32` | SHA256 of `tech_stack\|auth_model\|endpoint_pattern` | Always succeeds (deterministic) |
| Step parameters | `_interpolate_params` | `orchestrator.py:308` | `{{previous_outputs[N]}}` resolved; out-of-range preserved | Unresolved tokens left in place |
| HTTP response status | HTTPRequestHandler | `handlers/http_request_handler.py:17` | `status_code >= 400` → stderr = `"HTTP {code}"` | StepResult with stderr triggers failure handling |
| Failure type | `classify_failure` | `failure_classifier.py:6` | Status code + error string pattern match → FailureType enum | Falls through to SYSTEMIC |

### 3.2 Parsing

| Source Format | Target Format | Parser | Location |
|---------------|---------------|--------|----------|
| `>>> / <<<` traffic text | `(list[dict], list[dict])` requests + responses | `_parse_traffic_log` | `fingerprinter.py:29` |
| Binary .mitm file | `list[Flow]` mitmproxy objects | `FlowReader` via `_read_flows` | `recon_tools.py:17` |
| Binary .mitm file | Fingerprint (via intermediate text) | `fingerprint_from_mitm` | `capture/launcher.py:59` |
| HTTP body bytes | JSON object or truncated text | `_safe_json` | `recon_tools.py:66` |
| JWT Authorization header | Base64-decoded claims dict | `handle_jwt_decode` | `recon_tools.py:143` |
| Neo4j step parameters (JSON string) | Python dict | `json.loads` in `get_action_graph_with_steps` | `graph_repository.py:209` |
| Neo4j DateTime | ISO8601 string | `.isoformat()` in `get_action_graph_with_steps` | `graph_repository.py:209` |

### 3.3 Formatting

| Data | Formatter | Output Format | Purpose |
|------|-----------|---------------|---------|
| Flow objects | `_flow_summary` | One-line dict (method, URL, status, auth) | `recon_tools.py:27` — compact overview for Recon Agent |
| Flow objects | `_flow_detail` | Full req/resp dict with parsed bodies | `recon_tools.py:43` — detailed analysis for Agent |
| Similar fingerprints | `find_similar_action_graphs` | Multi-line `[Similar Graph N]` report | `graph_tools.py:36` — agent-readable knowledge |
| Repair edges | `get_repair_history` | Multi-line `[Repair N]` report | `graph_tools.py:93` — agent-readable history |
| API response content | `_summarize_content_blocks` | List[ContentBlockSummary] | `debug_logger.py:211` — debug tracing |

### 3.4 Enrichment

| Data | Enrichment | Source | Location |
|------|-----------|--------|----------|
| Fingerprint | observation_embedding (384-dim vector) | SentenceTransformer all-MiniLM-L6-v2 | `graph_tools.py:28` (lazy-loaded) |
| Compilation context | Repair context prepended | `assemble_repair_context()` — failed step + error + history | `context.py:64` |
| Step parameters | Auth headers injected | `_auth_headers(profile, token_ref)` based on auth_mechanism | `exploit_tools.py:69` |
| Step sequence | Login steps prepended | `_login_and_auth_steps(profile, user)` — 1-3 auth steps | `exploit_tools.py:15` |

---

## 4. Data Sources & Sinks

### 4.1 Entry Points

| Entry Point | Data Type | Source | First Handler |
|-------------|-----------|--------|---------------|
| Environment variables | Config strings | OS env / `.env` | `Settings()` (`config.py:6`) |
| `.mitm` capture file | Binary HTTP flows | mitmproxy recording | `fingerprint_from_mitm()` (`capture/launcher.py:59`) or `_read_flows()` (`recon_tools.py:17`) |
| Live HTTP target | HTTP responses | Target web app | `quick_fingerprint()` (`capture/launcher.py:20`) — 3 deterministic GET requests |
| Live proxy traffic | HTTP flows | mitmproxy intercepted | `LLMitMCaptureAddon.response()` (`capture/addon.py:18`) |
| Anthropic API responses | JSON with structured output | Claude model | `SimpleAgent.__call__()` (`agents.py:171`) or `ProgrammaticAgent.__call__()` (`agents.py:265`) |
| Neo4j query results | Dicts from Cypher | Neo4j database | `GraphRepository` methods (`graph_repository.py:16`) |

### 4.2 Exit Points

| Exit Point | Data Type | Destination | Final Handler |
|------------|-----------|-------------|---------------|
| Neo4j writes | Fingerprint, ActionGraph, Step, Finding nodes | Neo4j database | `GraphRepository.save_*()` methods |
| Console logging | OrchestratorResult summary | stdout | `main()` (`__main__.py:23`) logger.info calls |
| Debug JSON files | ApiCallLog, EventLog, RunSummary | `debug_logs/<timestamp>/` | `_write_json()` (`debug_logger.py:234`) |
| Temp files | HTTP response bodies | `llmitm_v2/tmp/` | HTTPRequestHandler (output_file param) |
| Capture JSON | Flow list | `/capture/flows.json` | `_write_flows_to_file()` (`capture/addon.py:33`) |
| Anthropic API calls | Prompts + tool results | Anthropic servers | `client.messages.parse()` / `client.beta.messages.create()` |

### 4.3 Storage Points

| Storage | Type | Read By | Written By |
|---------|------|---------|------------|
| Neo4j (:Fingerprint) | Node (hash, tech_stack, auth_model, endpoint_pattern, security_signals, observation_embedding) | `get_fingerprint_by_hash()`, `find_similar_fingerprints()` | `save_fingerprint()` |
| Neo4j (:ActionGraph) | Node + [:TRIGGERS] from Fingerprint | `get_action_graph_with_steps()`, `increment_execution_count()` | `save_action_graph()` |
| Neo4j (:Step) chain | Nodes + [:NEXT] + [:STARTS_WITH] | `get_action_graph_with_steps()`, `repair_step_chain()` | `save_action_graph()` |
| Neo4j (:Finding) | Node + [:PRODUCED_BY] to ActionGraph | Future analysis sessions | `save_finding()` |
| Neo4j [:REPAIRED_TO] | Relationship with reason + timestamp | `get_repair_history()` | `repair_step_chain()` |
| debug_logs/ | JSON files (call_NNN.json, event_NNN.json, run_summary.json) | Human review (offline) | `debug_logger` functions |
| llmitm_v2/tmp/ | Raw HTTP response bodies | RegexMatchHandler (via previous_outputs) | HTTPRequestHandler |

---

## 5. Complete Flow Examples

### Flow 1: Cold Start — Novel Target

```
ENV VARS (.env)
  │
  ▼
Settings() ──► target_profile="juice_shop", capture_mode="file"
  │               │
  │               ▼
  │         get_active_profile("juice_shop") → TargetProfile(auth_mechanism="bearer_token")
  │
  ▼
fingerprint_from_mitm("demo/juice_shop.mitm")
  │  FlowReader → parse flows → extract tech_stack/auth/endpoints/signals
  ▼
Fingerprint(tech_stack="Express", auth_model="JWT Bearer", endpoint_pattern="/api/*", hash="abc123")
  │
  ├──► graph_repo.save_fingerprint(fp) ──► Neo4j MERGE (:Fingerprint {hash:"abc123"})
  │
  ▼
_try_warm_start(fp) → get_action_graph_with_steps("abc123") → None
  │
  ▼
_compile(fp, mitm_file="demo/juice_shop.mitm")
  │
  │  assemble_recon_context(mitm_file) → context string with tool descriptions
  │  create_recon_agent(context) → ProgrammaticAgent (4 recon tools, max_iterations=12)
  │  create_attack_critic() → SimpleAgent (no tools, max_tokens=4096)
  │
  │  ┌─────────── Actor/Critic Loop (max 3 iterations) ──────────┐
  │  │ recon_agent(context, AttackPlan)                           │
  │  │   ├─ Agent writes Python in code_execution sandbox        │
  │  │   ├─ Calls response_inspect(mitm_file) → JSON summary    │
  │  │   ├─ Calls jwt_decode(mitm_file) → decoded claims        │
  │  │   └─ Returns AttackPlan via structured output             │
  │  │                                                           │
  │  │ attack_critic(plan.json(), AttackPlan) → refined plan     │
  │  └───────────────────────────────────────────────────────────┘
  │
  │  attack_plan_to_action_graph(refined_plan, profile)
  │    ├─ Iterates plan.attack_plan[] opportunities
  │    ├─ First compatible: EXPLOIT_STEP_GENERATORS["idor_walk"](path, obs, profile)
  │    │   ├─ _login_and_auth_steps(profile, "a") → [POST login, regex extract] (2 Steps)
  │    │   ├─ GET /api/Users/1 with Bearer token (1 Step)
  │    │   ├─ GET /api/Users/2 with Bearer token (1 Step, _increment_id)
  │    │   └─ OBSERVE step with success_criteria="." (1 Step)
  │    └─ ActionGraph(steps=[5 Steps], vulnerability_type="IDOR")
  │
  ├──► graph_repo.save_action_graph("abc123", ag) ──► Neo4j CREATE nodes + edges
  │
  ▼
_execute(ag, fp)
  │
  │  ctx = ExecutionContext(target_url, fp, previous_outputs=[], cookies={}, session_tokens={})
  │
  │  Step 0 (CAPTURE/HTTP_REQUEST): POST /rest/user/login {email, password}
  │    → httpx.post() → 200 '{"token":"eyJ..."}'
  │    → ctx.previous_outputs = ['{"token":"eyJ..."}']
  │
  │  Step 1 (ANALYZE/REGEX_MATCH): pattern='"token":"([^"]+)"' source="last"
  │    → re.search → group(1) = "eyJ..."
  │    → ctx.previous_outputs = ['{"token":"eyJ..."}', 'eyJ...']
  │
  │  Step 2 (CAPTURE/HTTP_REQUEST): GET /api/Users/1, Authorization: Bearer {{previous_outputs[1]}}
  │    → _interpolate_params resolves token
  │    → ctx.previous_outputs = [..., '{"id":1,"email":"admin@..."}']
  │
  │  Step 3 (MUTATE/HTTP_REQUEST): GET /api/Users/2, same Bearer token
  │    → ctx.previous_outputs = [..., '{"id":2,"email":"jim@..."}']
  │
  │  Step 4 (OBSERVE/HTTP_REQUEST): success_criteria="." matches non-empty
  │    → phase==OBSERVE + matched → Finding created
  │    ──► graph_repo.save_finding(ag.id, finding)
  │
  ├──► graph_repo.increment_execution_count(ag.id, True)
  ▼
OrchestratorResult(path="cold_start", compiled=True, repaired=False, execution={success=True, findings=[1]})
```

**Description**: A novel target is fingerprinted from a .mitm capture file. No matching ActionGraph exists in Neo4j, so the system enters cold start: the Recon Agent analyzes traffic via 4 recon tools, produces an AttackPlan, the Critic refines it, and deterministic exploit generators convert it to a 5-step ActionGraph. The graph is stored in Neo4j, then executed step-by-step with parameter interpolation threading outputs between steps. An OBSERVE-phase match produces a Finding.

**Data at each step**:
1. `.mitm` binary → Fingerprint (tech_stack, auth_model, endpoint_pattern, security_signals, hash)
2. Fingerprint hash → Neo4j lookup → miss → compilation context string
3. Context → Recon Agent → AttackPlan (list of AttackOpportunity with exploit_tool enum)
4. AttackPlan → Critic → refined AttackPlan → `attack_plan_to_action_graph()` → ActionGraph with 5 Steps
5. ActionGraph → step-by-step execution with ExecutionContext accumulating previous_outputs/tokens/cookies
6. OBSERVE match → Finding → Neo4j → OrchestratorResult

### Flow 2: Self-Repair — Systemic Failure

```
Fingerprint hash="abc123" → _try_warm_start → ActionGraph found (endpoints corrupted)
  │
  ▼
_execute(corrupted_ag, fp)
  │
  │  Steps 0-1 succeed (login + regex extract token)
  │  ctx.previous_outputs = ['{"token":"eyJ..."}', 'eyJ...']
  │
  │  Step 2: GET /api/Users/1 → HTTP 404
  │    → StepResult(stderr="HTTP 404", status_code=404)
  │
  ▼
_handle_step_failure(step=2, result, ctx, ag, retried=False)
  │
  │  classify_failure("HTTP 404", 404) → FailureType.SYSTEMIC
  │
  ▼
_repair(ag, step_2, "HTTP 404", ["login_response", "token"], fp)
  │
  │  assemble_repair_context(step_2, "HTTP 404", history)
  │    → "Step 2 (CAPTURE, http_request) failed. Error: HTTP 404..."
  │
  │  _compile(fp, mitm_file=..., repair_context="Step 2 failed...")
  │    → Recon Agent receives failure context prepended
  │    → Reanalyzes traffic, avoids broken endpoint
  │    → Critic refines → new ActionGraph
  │    ──► graph_repo.save_action_graph("abc123", new_ag) (newer created_at)
  │
  ▼
("repaired", new_ag) → _execute restarts with fresh ExecutionContext
  │  All steps succeed → Finding created
  ▼
OrchestratorResult(path="cold_start", compiled=True, repaired=True)
```

**Description**: A warm-started ActionGraph has corrupted endpoints. Step 2 returns HTTP 404, which `classify_failure()` maps to SYSTEMIC. The orchestrator calls `_repair()`, which prepends failure context to a fresh `_compile()` call. The Recon Agent reanalyzes traffic with knowledge of the failure, producing a corrected ActionGraph stored as a new Neo4j node (same fingerprint, newer timestamp). Execution restarts from step 0 with a fresh context and succeeds.

**Data at each step**:
1. Corrupted ActionGraph → execution fails at step 2 → StepResult with stderr="HTTP 404"
2. Error → `classify_failure("HTTP 404", 404)` → FailureType.SYSTEMIC
3. Failed step + error + history → `assemble_repair_context()` → enrichment string
4. Enrichment + original context → Recon Agent → Critic → new ActionGraph
5. New ActionGraph → fresh execution → success → OrchestratorResult(repaired=True)

### Flow 3: Warm Start — Zero LLM Cost

```
fingerprint_from_mitm("demo/juice_shop.mitm") → Fingerprint(hash="abc123")
  │
  ├──► graph_repo.save_fingerprint(fp) ──► Neo4j MERGE (no-op)
  │
  ▼
_try_warm_start(fp) → get_action_graph_with_steps("abc123")
  │  Neo4j: MATCH (f)-[:TRIGGERS]->(ag) ORDER BY ag.created_at DESC LIMIT 1
  │  + step chain traversal via [:STARTS_WITH] + [:NEXT*0..100]
  │  → Returns newest ActionGraph (repaired version if available)
  │
  ▼
ActionGraph(**neo4j_dict) → reconstructed with Step list
  │
  ▼
_execute(ag, fp)  ← Zero API calls, zero tokens
  │  Same deterministic step loop: HTTP → regex → Finding
  │
  ├──► graph_repo.increment_execution_count(ag.id, True)
  ▼
OrchestratorResult(path="warm_start", compiled=False, repaired=False)
```

**Description**: The same target is run again. Fingerprint hash matches an existing ActionGraph in Neo4j (ORDER BY created_at DESC selects the newest, including any repaired version). The graph executes deterministically with zero LLM involvement — only HTTP requests and regex matching. This demonstrates the "LLM is a compiler" thesis: expensive reasoning happens once, then the compiled artifact runs indefinitely at zero cost.

**Data at each step**:
1. .mitm file → Fingerprint (same hash as before)
2. Hash → Neo4j lookup → ActionGraph dict → `ActionGraph(**data)` reconstruction
3. Deterministic execution: HTTP requests + regex matches → Finding
4. OrchestratorResult(path="warm_start", compiled=False)

---

## Summary

### Flow Patterns

| Pattern | Usage | Locations |
|---------|-------|-----------|
| Fingerprint-driven routing | Every run: hash → Neo4j lookup → warm/cold branch | `orchestrator.py:79-120` |
| Parameter interpolation | Multi-step chains via `{{previous_outputs[N]}}` tokens | `orchestrator.py:308-327` |
| Context threading | ExecutionContext accumulates state across steps | `orchestrator.py:191-265`, all handlers |
| Actor/Critic refinement | Recon Agent generates → Critic refines (same schema) → deterministic conversion | `orchestrator.py:122-190`, `agents.py:347-420` |
| Deterministic-first classification | Pattern match status codes before LLM fallback | `failure_classifier.py:6` |
| Auth-mechanism branching | TargetProfile.auth_mechanism drives step generation | `exploit_tools.py:15-76` |
| Single-exploit-per-graph | First compatible exploit used, rest discarded | `orchestrator.py:43-67` |

### Data Lifecycle

| Data Type | Created | Transformed | Stored | Consumed | Destroyed |
|-----------|---------|-------------|--------|----------|-----------|
| Fingerprint | `fingerprint_from_mitm` or `quick_fingerprint` | `compute_hash()`, optional embedding | Neo4j MERGE (idempotent) | Every `run()` for routing | Never (accumulates) |
| ActionGraph | `_compile()` via LLM → `attack_plan_to_action_graph()` | Steps ordered, IDs generated | Neo4j CREATE | `_try_warm_start()` | Superseded by newer (ORDER BY DESC) |
| Step | Exploit generators (`exploit_tools.py`) | `_interpolate_params()` at execution | Neo4j as part of ActionGraph | `_execute()` step loop | Replaced by `repair_step_chain()` |
| Finding | `_execute()` on OBSERVE + criteria match | ID generated via `ensure_id()` | Neo4j CREATE + [:PRODUCED_BY] | Future analysis | Never (accumulates) |
| ExecutionContext | `_execute()` entry | Accumulates tokens/cookies/outputs | Memory only | Step handlers | Discarded at run end |
| AttackPlan | Recon Agent structured output | Critic refinement | Never persisted | `attack_plan_to_action_graph()` | Consumed immediately |
| StepResult | `handler.execute()` return | Evaluated for success/failure | Memory only | `_execute()` loop | Discarded after evaluation |

### Bottlenecks & Concerns

| Location | Issue | Impact | Recommendation |
|----------|-------|--------|----------------|
| `agents.py:44` | Token budget exhaustion | Repair cycles ~56K tokens; default budget 50K may be exceeded | Increase default or add per-phase budgets |
| `orchestrator.py:191` | Single-threaded step execution | Each step blocks on HTTP response; no parallelism | Acceptable for CAMRO sequential design |
| `graph_repository.py:116,265` | CREATE (not MERGE) for ActionGraph/Finding | Duplicate nodes on retry/crash | Switch to MERGE with id constraint |
| `http_request_handler.py` | No cleanup of `llmitm_v2/tmp/` files | Disk accumulation over repeated runs | Add cleanup in `_execute()` finally block |
| `debug_logger.py:234` | File writes unguarded (no try/except) | Disk-full → silent data loss | Add error handling in `_write_json()` |
| `models/context.py:11` | previous_outputs grows unbounded | Large HTTP responses accumulate in memory | Cap list size or truncate large outputs |
| `shell_command_handler.py:15` | subprocess shell=True | Command injection risk | Mitigated: steps are LLM-generated, not user-supplied |
