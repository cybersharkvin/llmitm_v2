# Project Progress

## Completed Features

- ✅ **Foundation → First E2E** (Feb 10-11): Pydantic models, GraphRepository, Neo4j schema, LLM agents (Strands SDK), step handlers (HTTP/Shell/Regex), orchestrator (cold/warm/repair), CLI, fingerprinting, snapshot infra, live recon agent. First Juice Shop cold+warm+self-repair verified. 87 tests. Commits: `9e58307`→`432a1c4` (14 commits)
- ✅ **Architecture Overhaul + Multi-Target** (Feb 12-14): Migrated Strands→Anthropic native SDK, consolidated to 2-agent arch (ProgrammaticAgent + SimpleAgent), built 4+5 tool system (4 recon + 5 exploit), added TargetProfile registry (Juice Shop/NodeGoat/DVWA with bearer/cookie/CSRF auth). Fixed ~25 bugs across 8 batches. All 3 targets pass all 4 modes. 112 tests. Commits: `a87073e`→`da4b447` (14 commits)
- ✅ **Final Polish** (Feb 15): Fixed HTTP 4xx stderr detection, 404→SYSTEMIC reclassification, IDOR auth offset bug. Added 7 boundary interaction tests. 119 tests, 0 failures. Commit: `b57e16e`

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
- StepType enum defines JSON_EXTRACT and RESPONSE_COMPARE but no handlers exist — get_handler() raises ValueError for these
- hooks/ directory is dead (only docstring __init__.py) — candidate for deletion
- MAX_CRITIC_ITERATIONS constant in constants.py is 5 but unused — config.py defaults to 3 and orchestrator reads from Settings

## Technical Debt

- setup_schema() runs on every CLI invocation (adds ~1s latency); could skip if schema exists
- APOC Cypher export in snapshot script fails silently (binary dump still works)
- demo/juice_shop_traffic.txt still exists but no longer referenced by config
- capture/flows.json (3.1M) and llmitm_v2/tmp/ are runtime artifacts tracked in git — should be gitignored
- capture/__init__.py is empty unlike other subpackages that re-export public names
- Docker Compose uses hardcoded credentials (Neo4j: `password`, MySQL: `dvwa`) — acceptable for local OWASP targets; `.env.example` covers onboarding
- `shell_command_handler.py` passes `step.command` to `subprocess.run(shell=True)` with no sanitization — low risk (steps are LLM-generated, not user-supplied) but worth noting
- `quick_fingerprint()` uses `verify=False` for TLS — acceptable for local testing, would need fixing for remote targets
- `debug_logs/` directory is a runtime artifact not gitignored — should be added alongside `llmitm_v2/tmp/`
- `debug_logger.py` file writes have no try/except — disk-full or permission errors cause silent data loss
- `save_action_graph()` and `save_finding()` use CREATE (not MERGE) — duplicates possible on retry/crash
- `addon.py:41` silently swallows `flows.json` write errors via `try/except pass`
- `ruff check` and `mypy` not included in `make test` or a `make lint` target — linting is manual only
- `black` declared as dev dep but redundant with `ruff format` — removal candidate
- No lock file for reproducible installs — adopt `uv` or commit `pip freeze` output
- `.venv/bin/` untracked binaries showing in git status — add to `.gitignore`
- CLI entry point uses `__main__.py` — could add `[project.scripts]` in pyproject.toml for cleaner invocation
- `previous_outputs` list in ExecutionContext grows unbounded — large HTTP responses accumulate in memory; should cap list size or truncate large outputs
- `debug_logger.py:234` `_write_json()` has no try/except — disk-full or permission errors cause silent data loss

## Version History

### Current State
- **Version**: 0.1.0
- **Status**: E2E VERIFIED — All 3 targets pass cold+warm+repair+persistence
- **Primary Branch**: main
- **Test Suite**: 119 passing, 1 skipped, 0 failed

### Recent Milestones
- **Feb 15, 2026**: Full Docker containerization — backend + frontend as compose services, Makefile simplified, single `docker compose up/down` workflow
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

- **Environment**: Fully containerized via Docker Compose (9 services)
- **Start**: `docker compose up -d` (starts Neo4j, targets, backend, frontend)
- **Stop**: `docker compose down`
- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:5001/health
- **Testing**: `make test` (uses local .venv)
- **Schema Setup**: `make schema`
- **Seed Demo**: `make seed`
- **Break for Repair Demo**: `make break-graph`

---

**Update Frequency**: After completing features or discovering issues
