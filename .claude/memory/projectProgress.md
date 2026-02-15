# Project Progress

## Completed Features

- ✅ **Foundation: Pydantic Data Models + GraphRepository**: Complete data layer foundation
  - Step models (CAMRO phases): CAPTURE, ANALYZE, MUTATE, REPLAY, OBSERVE
  - Fingerprint model with SHA256 hash computation
  - ActionGraph model with step chain and success rate metrics
  - Finding, CriticFeedback, RepairDiagnosis models for LLM integration
  - ExecutionContext, StepResult, CompilationContext, RepairContext for phases
  - Completed: Feb 10, 2026
  - Validation: 21 unit tests pass (test_models.py), all serialization round-trips verified

- ✅ **GraphRepository Pattern Implementation**: Core Neo4j access layer
  - save_fingerprint() — MERGE by hash (idempotent)
  - get_fingerprint_by_hash() — Exact lookup
  - find_similar_fingerprints() — Vector similarity search
  - save_action_graph() — Single transaction creates graph + steps + relationships
  - get_action_graph_with_steps() — Pre-loads full step chain via graph traversal
  - save_finding() — Creates Finding + [:PRODUCED_BY] edge
  - repair_step_chain() — Rewires [:NEXT] edges, creates [:REPAIRED_TO]
  - increment_execution_count() — Atomic metrics update
  - All queries parameterized, all access via managed transactions
  - Completed: Feb 10, 2026

- ✅ **Project Scaffolding**: Complete directory structure
  - llmitm_v2/{models,repository,__init__.py}
  - tests/{__init__.py,test_models.py,test_graph_repository.py}
  - Docker Compose (Neo4j 5, Juice Shop, mitmproxy)
  - pyproject.toml with all dependencies
  - .env.example, .gitignore
  - Completed: Feb 10, 2026

- ✅ **Neo4j Schema Setup**: Constraints and vector indexes
  - Fingerprint hash UNIQUE constraint
  - ActionGraph id UNIQUE constraint
  - Finding id UNIQUE constraint
  - Vector indexes for Fingerprint and Finding embeddings (384 dimensions)
  - Idempotent setup_schema.py script
  - Completed: Feb 10, 2026

- ✅ **Phase 2: Strands SDK Integration**: Complete LLM orchestration layer
  - Actor/Critic agent factories via Strands SDK with per-call structured_output_model
  - Context assembly (compilation_context, repair_context) with smart truncation
  - Deterministic failure classification (TRANSIENT_RECOVERABLE, TRANSIENT_UNRECOVERABLE, SYSTEMIC)
  - GraphTools with @tool methods: find_similar_action_graphs, get_repair_history
  - ApprovalHook for human-in-the-loop on destructive patterns
  - GraphRepository.get_repair_history() method for repair diagnostics
  - Graceful import fallbacks for Strands, Neo4j, sentence-transformers
  - Completed: Feb 10, 2026
  - Validation: 15 unit tests pass, 5 gracefully skip when dependencies unavailable

- ✅ **Phase 3: Step Handlers**: Complete execution layer
  - StepHandler ABC with execute(step, context) → StepResult contract
  - HTTPRequestHandler: httpx sync client, URL resolution, header/cookie merging, Set-Cookie extraction
  - ShellCommandHandler: subprocess.run with timeout, env vars, working dir, exit codes
  - RegexMatchHandler: pattern matching against previous_outputs with capture groups and source indexing
  - Handler registry: HANDLER_REGISTRY dict + get_handler() dispatch by StepType
  - ExecutionContext.cookies field added for cookie persistence across steps
  - Completed: Feb 10, 2026
  - Validation: 17 unit tests + 2 integration tests (58 total passing across all suites)

- ✅ **Phase 4: Orchestrator (Main Loop)**: Complete control flow
  - Orchestrator class with run() main entry point (cold/warm start decision)
  - _try_warm_start(): graph lookup by fingerprint hash (zero LLM)
  - _compile(): Actor/Critic loop with Strands __call__() API and structured_output_model
  - _execute(): Step walker with handler dispatch, context threading, finding collection
  - _interpolate_params(): {{previous_outputs[N]}} template substitution for dynamic values
  - _handle_step_failure(): 3-tier self-repair (retry/abort/repair)
  - _repair(): LLM-assisted RepairDiagnosis → repair_step_chain() in Neo4j
  - ExecutionResult and OrchestratorResult models
  - Completed: Feb 10, 2026
  - Validation: 70 tests passing (10 new), all ≤5 lines, no mocks

- ✅ **Phase 5: Hackathon Demo Infrastructure**: Complete CLI and fingerprinting
  - Fingerprinter class: rule-based HTTP traffic analysis for target identification
  - demo/juice_shop_traffic.txt: 8 pre-recorded request/response pairs for testing
  - CLI entry point (llmitm_v2/__main__.py): loads settings, fingerprints traffic, orchestrates execution
  - Bug fixes: (1) recursive interpolation for nested parameters, (2) repair uses fingerprint hash, (3) ExecutionResult.repaired propagates
  - Completed: Feb 11, 2026
  - Validation: 78 tests passing (6 new Fingerprinter + 2 new recursive interpolation tests)

- ✅ **Neo4j Graph Snapshot/Restore**: CI/CD for the database
  - Dual strategy: binary dump/load (fast) + APOC Cypher export (git-tracked, diffable)
  - Scripts: export-snapshot.sh, restore-snapshot.sh, reset-graph.sh
  - Makefile with snapshot/restore/reset/up/down/schema/test targets
  - docker-compose.yml updated with APOC file I/O + snapshots bind mount
  - Schema separated from data: setup_schema.py runs after every restore
  - Completed: Feb 11, 2026

- ✅ **Pre-E2E Audit: Model ID + Vector Dims + Doc Drift + Repair Bug**
  - Wired model_id through agent factories (env-configurable, default Haiku for cheap E2E)
  - Fixed hardcoded claude-sonnet-4-20250514 in agents.py → uses Settings.model_id
  - Fixed self-repair re-execution bug: repaired steps now re-run via index-based while loop
  - Fixed 1536→384 dimension refs in fingerprint.py, neo4jSchema.md, techContext.md
  - Fixed techContext.md schema drift: suggested_fix, Dict types match actual Pydantic models
  - Completed: Feb 11, 2026
  - Validation: 78 tests passing, 10 skipped, 0 regressions

- ✅ **E2E Cold Start + Warm Start Verified**: First live demo runs against Juice Shop
  - Fixed 7 integration bugs discovered during first real E2E run:
    1. `setup_schema` module vs function import in __main__.py
    2. Strands SDK import path: `strands.conversation` → `strands.agent` (NullConversationManager moved)
    3. API key not reaching Anthropic: added `api_key` param to agent factories, wired from Settings
    4. Actor max_tokens 4096 → 16384 (ActionGraph JSON too large for 4K)
    5. Critic max_tokens 1024 → 4096 (CriticFeedback structured output needs room)
    6. `STARTS_WITH` edge not created: hardcoded `order: 0` but LLM generates steps starting at 1; fixed to use MIN(order)
    7. Neo4j DateTime not serializable to Pydantic str: added `iso_format()` conversion in get_action_graph_with_steps
  - Also: `MaxTokensReachedException` added to compile loop catch block
  - Also: Makefile updated with `PYTHON` variable pointing to .venv, added `make run` target
  - Also: reset-graph.sh updated to use venv python
  - Cold start: Actor/Critic loop (3 iterations), compiled IDOR ActionGraph, executed 2 steps against live Juice Shop, found 1 vulnerability
  - Warm start: Zero LLM calls, graph fetched from Neo4j, executed 1 step, found 1 finding
  - Completed: Feb 11, 2026
  - Validation: 87 tests passing (previously skipped tests now run with full deps in venv), 1 skipped

- ✅ **Self-Repair Demo Infrastructure**: Break/fix graph scripts
  - scripts/break-graph.sh: Corrupts step 6 endpoint (/api/Users/1 → /api/Users/1/bogus-subpath)
  - scripts/fix-graph.sh: Reverses corruption (manual fallback)
  - Makefile targets: break-graph, fix-graph
  - Strategy: bogus subpath → 500/error → SYSTEMIC classification → LLM repair
  - Completed: Feb 11, 2026

- ✅ **All Three Hackathon Demos Verified**: Warm start, self-repair, persistence
  - Fixed 5 bugs: get_action_graph_with_steps (shortest→longest path), repair_step_chain (REPAIRED_TO edge fanout, DETACH DELETE syntax), Cypher quoting in break/fix scripts, snapshot file ownership
  - Added: seed-demo-graph.py (known-good 7-step IDOR graph), output_file support in HTTPRequestHandler, quiet mode for setup_schema, callback_handler=None for clean output, improved repair prompt
  - Repair uses critic agent (no tools) to avoid runaway tool-call loops
  - Run 1 (warm start): Success=True, 7 steps, 7 findings, 0 LLM calls
  - Run 2 (self-repair): Repaired=True, Success=True, 7 steps, 6 findings, 1 LLM call
  - Run 3 (persistence): Success=True, 6 steps, 6 findings, 0 LLM calls, [:REPAIRED_TO] edge verified
  - Snapshots: demo-baseline.dump, demo-with-repair.dump
  - Completed: Feb 11, 2026
  - Validation: 87 tests passing, 1 skipped

- ✅ **Live Recon Agent Integration**: LLM-driven active reconnaissance through mitmproxy
  - Recon models: ReconReport, DiscoveredEndpoint, AttackOpportunity, ReconCriticFeedback
  - Capture subsystem: mitmproxy addon, launcher (quick_fingerprint + run_recon), recon tools
  - Agent factories: create_recon_agent (tools), create_recon_critic_agent (no tools)
  - Context assembly: assemble_recon_context, assemble_compilation_context_from_recon
  - CLI: capture_mode=live/file branching with warm-start fast path
  - Completed: Feb 11, 2026
  - Validation: 100 tests passing (13 new), 1 skipped, 0 regressions

- ✅ **Live Recon E2E Bug Fixes**: 3 critical bugs preventing live pipeline execution
  - quick_fingerprint() sent requests to nonexistent proxy → fixed to send directly to target_url
  - Fingerprint hash mismatch: quick_fingerprint (deterministic) vs recon_report.to_fingerprint (LLM free-form) → reuse deterministic fingerprint as canonical hash
  - assemble_compilation_context_from_recon() was dead code → wired through orchestrator.run() and _compile() via Optional[ReconReport] param
  - Recon system prompt updated to warn shell_command bypasses capture proxy
  - Completed: Feb 11, 2026
  - Validation: 100 tests passing, 1 skipped, 0 regressions

- ✅ **Strands → Anthropic Native SDK Migration**: Replaced Strands SDK with Anthropic native structured output
  - agents.py: SimpleAgent (messages.parse) and ToolAgent (beta.messages.tool_runner) replace Strands Agent
  - tools: @beta_tool closures via create_recon_tools() and create_graph_tools() factories
  - orchestrator.py: Removed Strands exception imports, broad Exception catches
  - Expected API call reduction: ~1300 → ~16 per E2E run (grammar-constrained decoding vs fake tool calls)
  - Completed: Feb 12, 2026
  - Validation: 100 tests passing, 1 skipped, 0 regressions

- ✅ **API Cost Protections**: Defense-in-depth against runaway API costs
  - max_iterations on tool_runner: 20 for recon, 10 for actor-with-tools
  - Per-call token logging: model, input, output, cumulative/budget
  - Cumulative token budget: 500K tokens (~$0.25 worst case at Haiku), raises RuntimeError if exceeded
  - max_critic_iterations reduced 5→3 (6 API calls worst case instead of 10)
  - set_token_budget() wired from Settings via __main__.py
  - Completed: Feb 12, 2026
  - Validation: 100 tests passing, 1 skipped, 0 regressions

- ✅ **2-Agent Architecture Consolidation**: Programmatic tool calling + skill guides
  - Consolidated 4 agents (actor, critic, recon, recon_critic) into 2 (Recon Agent + Attack Critic)
  - ProgrammaticAgent: code_execution sandbox + mitmdump tool (agent writes Python, intermediate results stay in sandbox)
  - SimpleAgent: unchanged, used for Attack Critic
  - Skill guides: 4 markdown files (mitmdump, initial_recon, lateral_movement, persistence) loaded into system prompt
  - Unified .mitm binary format for both file and live modes
  - Token budget tightened 500K→50K
  - Removed: ToolAgent, ApprovalHook, ReconCriticFeedback, assemble_compilation_context[_from_recon]
  - Completed: Feb 12, 2026
  - Validation: 98 tests passing, 1 skipped, 0 regressions

- ✅ **Bug Fixes + Dead Code Cleanup**: 4 bugs fixed, 2 dead models removed
  - Bug 1: RegexMatchHandler source param — try/except around int() prevents crash on interpolated values
  - Bug 2: Repair agent wrong system prompt — added REPAIR_SYSTEM_PROMPT + create_repair_agent() factory
  - Bug 3: File mode required live target — added fingerprint_from_mitm() for offline fingerprinting from .mitm files
  - Bug 4: Findings created for all steps — now only OBSERVE-phase steps produce findings
  - Dead code: Removed CompilationContext and RepairContext models (never constructed)
  - Completed: Feb 12, 2026
  - Validation: 99 tests passing, 1 skipped, 0 regressions

- ✅ **Unified Repair + FlowReader Fix**: Architectural cleanup + blocking bug fix
  - fingerprint_from_mitm() rewritten with FlowReader (fixes format mismatch — was producing "Unknown" fingerprint)
  - Repair unified into _compile() with repair_context enrichment (no separate repair agent)
  - Deleted: REPAIR_SYSTEM_PROMPT, create_repair_agent()
  - repair_step_chain() NEXT rewiring fixed (HAS_STEP-scoped queries)
  - _execute() restarts from i=0 on repair (new graph = fresh execution)
  - Completed: Feb 12, 2026
  - Validation: 98 tests passing, 1 skipped, 0 regressions

- ✅ **Bug Fix Batch (12-Issue Audit)**: 8 bugs fixed across 6 files
  - B1: Removed dead strands deps, added mitmproxy>=10.0 to pyproject.toml
  - B1+S1: Resolved mitmdump from venv bin dir, shlex.split + list-form subprocess (no shell injection)
  - B2: HTTPRequestHandler uses json= kwarg for dict bodies (was crashing httpx)
  - B3: _repair() uses self._mitm_file/self._proxy_url (absolute paths stored in run())
  - B4: previous_outputs.append moved after failure check (no double-append on retry)
  - B5: get_action_graph_with_steps() selects newest AG by created_at DESC
  - B6: Added extract_token_path param for session_tokens["Authorization"] extraction
  - C1: OrchestratorResult.path = "repair" when repaired
  - T1: ExecutionResult.findings: List[Finding] (was List[Any])
  - C2: OrchestratorResult.path: Literal["cold_start", "warm_start", "repair"]
  - Deferred: T2 (AgentResult generic), T3 (stringly-typed failure return)
  - Completed: Feb 12, 2026
  - Validation: 98 tests passing, 1 skipped, 0 regressions

- ✅ **Debug Logging for Agent Pipeline**: Opt-in per-call tracing for E2E debugging
  - `llmitm_v2/debug_logger.py`: Pydantic models (ApiCallLog, EventLog, RunSummary) + module-level no-op functions
  - Per-API-call JSON dumps (call_NNN.json) with tokens, stop_reason, content blocks, tool calls
  - Per-orchestrator-event JSON dumps (event_NNN_<type>.json) for compile_iter, critic_result, step_result, failure
  - run_summary.json with aggregated stats, fires even on crash via try/finally in __main__.py
  - Wired into SimpleAgent, ProgrammaticAgent, Orchestrator._compile/_execute/_handle_step_failure
  - Enabled via `DEBUG_LOGGING=true` env var; zero overhead when disabled
  - Completed: Feb 13, 2026
  - Validation: 98 tests passing, 1 skipped, 0 regressions

- ✅ **ProgrammaticAgent E2E Fixes (prev session)**: 5 bugs + model switch for programmatic tool calling
  - Switched model_id default from Haiku to Sonnet 4.5 (Haiku lacks programmatic tool calling support)
  - Fixed parse() vs create() for output_format, container_id tracking, _sanitize_content, input dict handling
  - Captured demo/juice_shop.mitm (35KB, 7 flows)
  - Completed: Feb 12-13, 2026

- ✅ **4+5 Tool Architecture**: Grammar-enforced recon + deterministic exploit step generation
  - 4 recon tools: response_inspect, jwt_decode, header_audit, response_diff (FlowReader-based)
  - 5 exploit tools: idor_walk, auth_strip, token_swap, namespace_probe, role_tamper (CAMRO step generators)
  - AttackPlan model with ReconTool/ExploitTool Literal enums (grammar-constrained)
  - Critic refines AttackPlan (same schema) instead of pass/fail CriticFeedback
  - attack_plan_to_action_graph() deterministic conversion (zero LLM)
  - Skill guides rewritten for new tools (recon_tools.md replaces mitmdump.md)
  - Removed: ReconReport, DiscoveredEndpoint, old mitmdump tool
  - Completed: Feb 13, 2026
  - Validation: 96 tests passing, 1 skipped, 0 regressions

- ✅ **Pre-E2E Bug Fixes (4 bugs)**: Credential placeholders, URL resolution, break-graph targeting
  - Bug A: Replaced {{EMAIL}}/{{PASSWORD}} placeholders in exploit_tools.py with actual Juice Shop creds via _CREDS dict
  - Bug B: HTTPRequestHandler URL resolution now falls back to parameters["path"] before step.command
  - Bug C+D: break-graph.sh rewritten to corrupt HTTP method (GET→PATCH) on any /api/Users step, ensuring 500→SYSTEMIC (not 404→abort)
  - Completed: Feb 13, 2026
  - Validation: 96 tests passing, 1 skipped, 0 regressions

- ✅ **Bug 5 Fix: capture_group defaults to 0 (BLOCKING)**: Token extraction regex steps
  - All 5 token extraction regex steps in exploit_tools.py now set `"capture_group": 1`
  - Without this, `match.group(0)` returned `"token":"eyJ..."` instead of just the JWT
  - Downstream: malformed `Authorization: Bearer "token":"eyJ..."` → 401 → abort
  - Affected: idor_walk, auth_strip, token_swap (x2), role_tamper
  - Completed: Feb 13, 2026
  - Validation: 96 tests passing, 1 skipped, 0 regressions

- ✅ **E2E All 4 Tests PASSING**: Full pipeline verified against live Juice Shop
  - Fixed 6 bugs during E2E: skill guide bloat, max_iterations too high, {id} template in exploit_target, step.type.value on string, multi-exploit token explosion, runaway repair cycles
  - Removed skill guides from Recon Agent system prompt (~2.9K tokens saved per call)
  - Added Pydantic field_validator on exploit_target (auto-fix {id}→1, strip full URLs to paths)
  - Capped to 1 exploit per ActionGraph (prevents cascading failures)
  - Single-repair guard (abort on second failure after repair)
  - Test 1 Cold Start: 7 API calls, ~37K tokens, 5 steps, 1 IDOR finding
  - Test 2 Warm Start: 0 API calls, 0 tokens, 5 steps, 1 IDOR finding
  - Test 3 Self-Repair: 9 API calls, ~56K tokens, 8 steps (3 failed + 5 clean), 1 IDOR finding
  - Test 4 Persistence: 0 API calls, 0 tokens, 5 steps, 1 IDOR finding
  - Completed: Feb 13, 2026
  - Validation: 96 tests passing, 1 skipped, 0 regressions

- ✅ **Multi-Target Support: NodeGoat + DVWA**: Target profile registry + multi-auth exploit steps
  - TargetProfile Pydantic model with auth_mechanism Literal discriminator (bearer_token / session_cookie)
  - TARGET_PROFILES registry: juice_shop (bearer), nodegoat (session cookie), dvwa (session cookie + CSRF)
  - _login_and_auth_steps() produces 1-3 steps depending on auth mechanism
  - skip_cookies parameter in HTTPRequestHandler for auth_strip on cookie targets
  - token_swap raises ValueError for cookie auth (caught by attack_plan_to_action_graph)
  - Docker Compose services for nodegoat, dvwa, mongo, mysql
  - Makefile targets: run-nodegoat, run-dvwa, break-graph-nodegoat, break-graph-dvwa
  - Completed: Feb 13, 2026
  - Validation: 112 tests passing (16 new), 1 skipped, 0 regressions

- ✅ **GAP-3 Closed: Multi-Target E2E Verified**: All 3 targets pass cold+warm start
  - Captured demo/nodegoat.mitm (54KB, 7 flows) and demo/dvwa.mitm (34KB, CSRF login flow)
  - Fixed HTTPRequestHandler: form encoding (data= instead of json=) for HTML apps
  - Fixed HTTPRequestHandler: follow_redirects=True (httpx defaults to False)
  - Fixed exploit_tools: generic success criteria "." instead of JSON-specific patterns
  - Fixed attack_plan_to_action_graph: try all exploits until compatible one found (was only trying first)
  - Added extra_login_fields to TargetProfile for DVWA's Login=Login submit button
  - ProgrammaticAgent max_iterations 8→12 for complex targets
  - NodeGoat built from OWASP/NodeGoat source (owasp-nodegoat:local), needs db-reset on first run
  - Juice Shop: cold=38K tokens, warm=0 | NodeGoat: cold=87K, warm=0 | DVWA: cold=71K, warm=0
  - Completed: Feb 14, 2026
  - Validation: 112 tests passing, 1 skipped, 0 regressions

- ✅ **Self-Repair Verified on All 3 Targets + 3 Bug Fixes**: Full 4-mode demo verified
  - Bug 1: HTTP 4xx responses not treated as failures — HTTPRequestHandler now sets stderr for status >= 400
  - Bug 2: 404 classified as TRANSIENT_UNRECOVERABLE (abort) — reclassified as SYSTEMIC (triggers repair)
  - Bug 3: IDOR MUTATE step auth offset off-by-one — offset+1 → offset in exploit_tools.py
  - All 3 targets pass cold→warm→repair→persistence
  - Juice Shop repair: ~134K tokens | NodeGoat repair: ~70K tokens | DVWA repair: ~60K tokens
  - README updated with multi-target results, setup instructions, break/repair commands
  - Completed: Feb 15, 2026
  - Validation: 112 tests passing, 1 skipped, 0 regressions

- ✅ **Boundary Interaction Tests**: 7 tests covering cross-component failure modes
  - test_http_4xx_sets_stderr: HTTP handler sets stderr for 404 responses (integration, NodeGoat)
  - test_http_2xx_has_empty_stderr: HTTP handler leaves stderr empty for 200 responses
  - test_idor_mutate_bearer_references_token_not_login_response: MUTATE step uses previous_outputs[-2] (JWT), not [-3] (login body)
  - test_idor_capture_bearer_references_last_output: CAPTURE step uses previous_outputs[-1] (JWT)
  - test_idor_cookie/csrf_steps_have_no_auth_offset_issue: cookie-auth steps don't have output references in headers
  - test_token_swap_replay_uses_user_b_token: REPLAY step uses User B's token (previous_outputs[-1])
  - Completed: Feb 15, 2026
  - Validation: 119 tests passing (7 new), 1 skipped, 0 regressions

## In Progress

- None

## Pending Features

- Pre-recorded demo capture (terminal session + Neo4j Browser screenshots)

## Known Issues

- CriticFeedback model still exists but no longer used in _compile() (dead code candidate)
- graph_tools.py still uses @beta_tool closures — may need update if tool_runner is fully removed
- Skill guides exist in skills/ but are not loaded (disabled for token efficiency)
- T2: AgentResult.structured_output: Any — needs Generic[T] (deferred)
- T3: _handle_step_failure stringly-typed return — needs enum/dataclass (deferred)

## Technical Debt

- setup_schema() runs on every CLI invocation (adds ~1s latency); could skip if schema exists
- APOC Cypher export in snapshot script fails silently (binary dump still works)
- demo/juice_shop_traffic.txt still exists but no longer referenced by config

## Version History

### Current State
- **Version**: 0.1.0
- **Status**: E2E VERIFIED — All 3 targets pass cold+warm+repair+persistence
- **Primary Branch**: main
- **Test Suite**: 119 passing, 1 skipped, 0 failed

### Recent Milestones
- **Feb 15, 2026**: Boundary interaction tests added (7 new tests: HTTP 4xx stderr, auth token output references, token_swap User B ref). 119 tests total.
- **Feb 15, 2026**: Self-repair verified on all 3 targets (3 bugs fixed: HTTP 4xx stderr, 404→SYSTEMIC, auth offset). README updated. PR ready.
- **Feb 14, 2026**: GAP-3 CLOSED — Multi-target E2E verified (Juice Shop 38K, NodeGoat 87K, DVWA 71K cold; all 0 tokens warm)
- **Feb 13, 2026**: E2E ALL 4 TESTS PASSING (cold start 37K tokens, warm start 0 tokens, self-repair 56K tokens, persistence 0 tokens)
- **Feb 13, 2026**: Pre-E2E bug fixes (credential placeholders, URL resolution, break-graph method corruption, 96 tests)
- **Feb 13, 2026**: 4+5 tool architecture (4 recon tools + 5 exploit tools, AttackPlan model, deterministic step generation, 96 tests)
- **Feb 13, 2026**: Debug logging for agent pipeline (opt-in per-call JSON tracing, 98 tests)
- **Feb 12-13, 2026**: ProgrammaticAgent E2E fixes (5 bugs, Haiku→Sonnet, juice_shop.mitm capture)
- **Feb 12, 2026**: Bug fix batch — 8 bugs fixed across 6 files (command injection, httpx dict body, orchestrator paths, newest AG selection, type safety)
- **Feb 12, 2026**: Unified repair + FlowReader fix (fingerprint_from_mitm, _compile(repair_context=), deleted repair agent, 98 tests)
- **Feb 12, 2026**: Bug fixes + dead code cleanup (4 bugs, 2 dead models removed, 99 tests)
- **Feb 12, 2026**: 2-agent architecture consolidation (ProgrammaticAgent + skill guides + .mitm format + 50K budget)
- **Feb 12, 2026**: API cost protections (max_iterations, token logging, cumulative budget, max_critic_iterations 5→3)
- **Feb 12, 2026**: Strands → Anthropic native SDK migration (SimpleAgent/ToolAgent, @beta_tool, grammar-constrained structured output)
- **Feb 11, 2026**: Live recon E2E bug fixes (3 critical: proxy routing, hash mismatch, dead code wiring)
- **Feb 11, 2026**: All three hackathon demos verified (warm start, self-repair, persistence) — 5 bugs fixed, demo polished
- **Feb 11, 2026**: E2E cold start + warm start verified against live Juice Shop (7 integration bugs fixed)
- **Feb 11, 2026**: Pre-E2E audit fixes (model_id wiring, vector dim corrections, repair re-execution bug)
- **Feb 11, 2026**: Neo4j snapshot/restore infrastructure (Makefile, scripts, dual backup strategy)
- **Feb 11, 2026**: Phase 5 complete (Fingerprinter, demo traffic, CLI, bug fixes: 78 tests passing)
- **Feb 10, 2026**: Phase 4 complete (Orchestrator main loop: cold/warm/repair flows, 70 tests passing)
- **Feb 10, 2026**: Phase 3 complete (Step Handlers: HTTP, Shell, Regex + registry, 58 tests passing)
- **Feb 10, 2026**: Phase 2 complete (Strands SDK integration, agents, context assembly, failure classification)
- **Feb 10, 2026**: Foundation complete (Pydantic models, GraphRepository, Neo4j schema)

## Deployment Status

- **Environment**: Local development (Docker Compose + .venv)
- **Installation**: `python3 -m venv .venv && .venv/bin/pip install -e .`
- **Run**: `make run` or `.venv/bin/python3 -m llmitm_v2`
- **Schema Setup**: `make schema`
- **Testing**: `make test`
- **Snapshot**: `make snapshot NAME=x`
- **Restore**: `make restore NAME=x`
- **Reset**: `make reset` (online wipe + schema recreate)
- **Seed Demo**: `make seed` (insert known-good IDOR ActionGraph)
- **Break for Repair Demo**: `make break-graph` (corrupt GET→PATCH on /api/Users steps)
- **Fix Manually**: `make fix-graph` (reverse corruption)

---

**Update Frequency**: After completing features or discovering issues
