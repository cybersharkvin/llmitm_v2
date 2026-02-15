# Overall Project Structure Analysis

*Generated from direct codebase exploration on Feb 15, 2026. Source: filesystem listing, `wc -l`, reading all 37 source files + config files.*

## 1. Directory Structure

### 1.1 Complete Directory Tree

From `find` output (excluding `.git`, `.venv`, `__pycache__`, `debug_logs`, `.claude/docs`):

```
llmitm_v2/                              # Project root (git repo)
├── llmitm_v2/                          # Main source package
│   ├── __init__.py                     # Exports Fingerprinter + __version__
│   ├── __main__.py                     # CLI entry point: main()
│   ├── config.py                       # Settings(BaseSettings) — 20+ env vars
│   ├── constants.py                    # 3 enums (StepPhase, StepType, FailureType) + 5 constants
│   ├── debug_logger.py                 # Opt-in JSON tracing (DEBUG_LOGGING env var)
│   ├── fingerprinter.py                # Rule-based HTTP traffic parser → Fingerprint
│   ├── target_profiles.py              # 3 target profiles (juice_shop, nodegoat, dvwa)
│   ├── capture/                        # Traffic capture subsystem
│   │   ├── __init__.py                 # Empty
│   │   ├── addon.py                    # mitmproxy addon (LLMitMCaptureAddon)
│   │   ├── launcher.py                 # quick_fingerprint() + fingerprint_from_mitm()
│   │   └── flows.json                  # 3.1M runtime artifact (should be gitignored)
│   ├── handlers/                       # Step execution — ABC + 3 implementations
│   │   ├── __init__.py                 # Re-exports all handlers + registry
│   │   ├── base.py                     # StepHandler(ABC) — abstract execute()
│   │   ├── http_request_handler.py     # httpx sync client, form/JSON encoding, cookie tracking
│   │   ├── shell_command_handler.py    # subprocess.run with timeout + env vars
│   │   ├── regex_match_handler.py      # Pattern matching against previous_outputs
│   │   └── registry.py                 # HANDLER_REGISTRY dict + get_handler() dispatch
│   ├── hooks/                          # DEAD MODULE — ApprovalHook removed, only docstring __init__
│   │   └── __init__.py
│   ├── models/                         # 18 Pydantic models across 7 files
│   │   ├── __init__.py                 # Re-exports 11 models in __all__
│   │   ├── step.py                     # Step (CAMRO phase + type + command + params)
│   │   ├── fingerprint.py              # Fingerprint (SHA256 hash, 384-dim embedding)
│   │   ├── action_graph.py             # ActionGraph (UUID id, steps list, metrics)
│   │   ├── context.py                  # ExecutionContext, StepResult, ExecutionResult, OrchestratorResult
│   │   ├── finding.py                  # Finding (vulnerability observation)
│   │   ├── critic.py                   # CriticFeedback, RepairDiagnosis
│   │   └── recon.py                    # AttackOpportunity, AttackPlan (Literal enums for LLM)
│   ├── orchestrator/                   # Core control flow
│   │   ├── __init__.py                 # Re-exports 6 items
│   │   ├── agents.py                   # ProgrammaticAgent + SimpleAgent + 2 factory functions
│   │   ├── orchestrator.py             # Orchestrator class (run/compile/execute/repair)
│   │   ├── context.py                  # assemble_recon_context() + assemble_repair_context()
│   │   └── failure_classifier.py       # classify_failure() — deterministic status code mapping
│   ├── repository/                     # Neo4j data access layer
│   │   ├── __init__.py                 # Re-exports GraphRepository
│   │   ├── graph_repository.py         # 492 LOC — all Cypher behind semantic methods
│   │   └── setup_schema.py             # Constraints + vector indexes (idempotent)
│   └── tools/                          # LLM tool implementations
│       ├── __init__.py                 # Re-exports GraphTools
│       ├── recon_tools.py              # 4 FlowReader-based tools (TOOL_SCHEMAS + TOOL_HANDLERS)
│       ├── exploit_tools.py            # 5 step generators (EXPLOIT_STEP_GENERATORS dict)
│       └── graph_tools.py              # GraphTools class + create_graph_tools() factory
├── tests/                              # 8 test files, 1093 LOC
│   ├── __init__.py                     # Empty
│   ├── test_models.py                  # 152 LOC — Pydantic model tests
│   ├── test_handlers.py                # 175 LOC — Handler execution tests
│   ├── test_orchestrator.py            # 158 LOC — Orchestrator logic tests
│   ├── test_orchestrator_main.py       # 132 LOC — Main loop tests
│   ├── test_graph_repository.py        # 159 LOC — Neo4j integration tests
│   ├── test_fingerprinter.py           # 120 LOC — Fingerprinting tests
│   ├── test_recon_models.py            # 66 LOC — Recon model tests
│   └── test_target_profiles.py         # 130 LOC — Multi-target profile tests
├── scripts/                            # Shell automation
│   ├── break-graph.sh                  # Corrupt graph for repair demo
│   ├── fix-graph.sh                    # Reverse corruption
│   ├── export-snapshot.sh              # Binary dump + APOC export
│   ├── restore-snapshot.sh             # Binary load + schema recreate
│   ├── reset-graph.sh                  # Online wipe + schema recreate
│   └── seed-demo-graph.py              # 199 LOC — Insert known-good IDOR ActionGraph
├── demo/                               # Pre-recorded traffic captures
│   ├── juice_shop.mitm                 # 36K — Juice Shop (7 flows)
│   ├── nodegoat.mitm                   # 54K — NodeGoat (7 flows)
│   ├── dvwa.mitm                       # 33K — DVWA (CSRF login flow)
│   └── juice_shop_traffic.txt          # 3.5K — Human-readable format (LEGACY, unreferenced)
├── skills/                             # LLM methodology guides (DISABLED in code)
│   ├── initial_recon.md
│   ├── lateral_movement.md
│   ├── persistence.md
│   └── recon_tools.md
├── backups/                            # Neo4j database dumps
│   ├── demo-baseline.dump
│   ├── demo-cold-warm-working.dump
│   └── demo-with-repair.dump
├── llmitm_v2.egg-info/                 # Editable install metadata (auto-generated)
├── docker-compose.yml                  # 7 services
├── Makefile                            # 18 targets
├── pyproject.toml                      # Package config + tool settings
├── README.md                           # Project docs
├── .env / .env.example                 # Environment config
├── hackathon_event_details.md          # Event context
├── mitmdump-cheatsheet.md              # Reference docs
├── Mitmproxy_for_Penetration_Testing_A_Professional_Guide.md
└── LICENSE                             # MIT
```

### 1.2 File Counts by Directory

Counted from filesystem listing:

| Directory | .py | .sh | .md | .mitm/.dump | Config | Total |
|-----------|-----|-----|-----|-------------|--------|-------|
| `llmitm_v2/` | 37 | 0 | 0 | 0 | 0 | 37 (+flows.json, tmp/) |
| `tests/` | 9 | 0 | 0 | 0 | 0 | 9 |
| `scripts/` | 1 | 5 | 0 | 0 | 0 | 6 |
| `demo/` | 0 | 0 | 0 | 3 | 0 | 3 (+1 legacy .txt) |
| `skills/` | 0 | 0 | 4 | 0 | 0 | 4 |
| `backups/` | 0 | 0 | 0 | 3 | 0 | 3 |
| Root | 0 | 0 | 5 | 0 | 5 (.yml/.toml/.env×2/.gitignore) | 10 |
| **Total** | **47** | **5** | **9** | **6** | **5** | **72+** |

---

## 2. Component Categories

Derived from reading actual imports and class definitions in all 37 source files:

### 2.1 Component Inventory

| Category | What I Found (from imports + definitions) | Location |
|----------|------------------------------------------|----------|
| **Data Models** | 18 Pydantic BaseModel subclasses across 7 files. `models/__init__.py` re-exports 11 of these. Two are LLM-output schemas (AttackPlan, AttackOpportunity) with Literal-typed fields for grammar-constrained decoding. | `models/` |
| **Orchestration** | Orchestrator class (343 LOC) owns all control flow. Two agent classes: SimpleAgent (single-shot `messages.parse`) and ProgrammaticAgent (code_execution sandbox + tool loop). Two context assembler functions. One failure classifier function. | `orchestrator/` |
| **Execution** | StepHandler ABC defines `execute(step, context) → StepResult`. 3 concrete handlers: HTTP (httpx), Shell (subprocess), Regex. Registry maps StepType → handler class. **Note: StepType enum has 5 values but only 3 have handlers** — `JSON_EXTRACT` and `RESPONSE_COMPARE` are defined but unimplemented. | `handlers/` |
| **Data Access** | GraphRepository (492 LOC, largest file) wraps all Neo4j Cypher in managed transactions. setup_schema creates constraints + vector indexes. **Graceful import fallback** — Neo4j driver is optional (try/except on import). | `repository/` |
| **Tools** | 4 recon tools (FlowReader-based .mitm analysis) exported as TOOL_SCHEMAS + TOOL_HANDLERS dicts. 5 exploit step generators exported as EXPLOIT_STEP_GENERATORS dict. GraphTools class with @beta_tool closures (used for embedding-based Neo4j queries). | `tools/` |
| **Capture** | LLMitMCaptureAddon (mitmproxy response hook). Two fingerprint functions: quick_fingerprint (live httpx probes) and fingerprint_from_mitm (offline FlowReader). `capture/__init__.py` is empty — no re-exports. | `capture/` |
| **Configuration** | Settings(BaseSettings) loads from .env — 20+ fields covering Neo4j, Anthropic, target, compilation, capture mode. TargetProfile registry: 3 hardcoded profiles with auth mechanism discriminator. 3 enums + 5 constants in constants.py. | Root-level `.py` files |
| **Diagnostics** | Fingerprinter class (deterministic HTTP traffic → Fingerprint). debug_logger module (opt-in JSON tracing, no-op when disabled). | Root-level `.py` files |
| **Dead Code** | `hooks/` module — only contains docstring saying "ApprovalHook removed." `CriticFeedback` model defined in `models/critic.py` but not imported by orchestrator (only `RepairDiagnosis` is used). | `hooks/`, `models/critic.py` |

### 2.2 Component Relationships (from actual import graph)

```
__main__.py
├── imports config.Settings
├── imports target_profiles.get_active_profile
├── imports orchestrator.Orchestrator
├── imports repository.GraphRepository
├── imports repository.setup_schema
├── imports capture.launcher (fingerprint_from_mitm, quick_fingerprint)
├── imports debug_logger (init, write_summary)
└── imports orchestrator.agents (set_token_budget)

orchestrator.orchestrator
├── imports orchestrator.agents (create_recon_agent, create_attack_critic)
├── imports orchestrator.context (assemble_recon_context, assemble_repair_context)
├── imports orchestrator.failure_classifier (classify_failure)
├── imports handlers.registry (get_handler)
├── imports repository.GraphRepository
├── imports tools.exploit_tools (EXPLOIT_STEP_GENERATORS)
├── imports target_profiles (get_active_profile, TargetProfile)
├── imports debug_logger (log_event)
└── imports models (ActionGraph, Step, Fingerprint, Finding, etc.)

orchestrator.agents
├── imports anthropic (SDK client)
├── imports debug_logger (log_api_call, ToolCallRecord)
└── imports tools.recon_tools (TOOL_SCHEMAS, TOOL_HANDLERS)

handlers/* → imports models (Step, ExecutionContext, StepResult)
tools/exploit_tools → imports models.step, constants, target_profiles
tools/recon_tools → imports mitmproxy.io.FlowReader
tools/graph_tools → imports anthropic.beta_tool, repository.GraphRepository
models/* → imports only from within models/ and constants
```

**Key insight from imports:** The dependency graph is strictly layered — models depend on nothing external, handlers depend only on models, tools depend on models + external libs, orchestrator depends on everything. No circular imports observed.

---

## 3. Naming Conventions

Observed from reading actual source code:

### 3.1 Extension Usage

| Extension | Count | Observed Purpose |
|-----------|-------|-----------------|
| `.py` | 47 (37 source + 9 test + 1 script) | All code |
| `.sh` | 5 | Neo4j/graph automation scripts |
| `.md` | 9 project-level | Docs, skill guides, cheatsheets |
| `.mitm` | 3 | Binary mitmproxy captures (demo/) |
| `.dump` | 3 | Neo4j binary database dumps (backups/) |
| `.yml` | 1 | Docker Compose |
| `.toml` | 1 | pyproject.toml |
| `.json` | 3+ | flows.json, settings.json, tmp/ files |

### 3.2 Naming Patterns (from actual code)

| Element | Pattern Observed | Examples from Code |
|---------|-----------------|-------------------|
| Classes (Pydantic) | PascalCase noun | `Fingerprint`, `ActionGraph`, `AttackPlan`, `TargetProfile` |
| Classes (ABC) | PascalCase, inherits `ABC` directly | `StepHandler(ABC)` in `base.py:9` |
| Classes (handler) | PascalCase ending in `Handler` | `HTTPRequestHandler`, `ShellCommandHandler`, `RegexMatchHandler` |
| Enums | PascalCase, `(str, Enum)` mixin | `StepPhase`, `StepType`, `FailureType` |
| Factory functions | `create_` prefix | `create_recon_agent()`, `create_attack_critic()`, `create_graph_tools()` |
| Public functions | snake_case verb phrase | `classify_failure()`, `assemble_recon_context()`, `get_active_profile()` |
| Private functions | `_` prefix | `_auth_headers()`, `_flow_detail()`, `_safe_json()`, `_truncate_dict()` |
| Constants | UPPER_SNAKE_CASE | `HANDLER_REGISTRY`, `TARGET_PROFILES`, `EXPLOIT_STEP_GENERATORS`, `MAX_CRITIC_ITERATIONS` |
| Test classes | `Test` prefix | `TestActionGraph`, `TestFailureClassification` |
| Test functions | `test_` prefix, descriptive | `test_classify_failure_404_is_systemic()` |
| Files | snake_case | `graph_repository.py`, `exploit_tools.py`, `failure_classifier.py` |

### 3.3 Directory Naming

| Pattern | Observed | Examples |
|---------|----------|---------|
| Singular | Conceptual subsystem | `capture/`, `repository/` |
| Plural | Collection of similar items | `models/`, `handlers/`, `tools/` |
| Layer-based grouping | Code grouped by architectural role | `models` (data), `handlers` (execution), `orchestrator` (control), `repository` (persistence), `tools` (LLM capabilities) |

---

## 4. Project Type

### 4.1 Framework/Platform (from pyproject.toml + actual imports)

| Aspect | Observed |
|--------|---------|
| **Primary Framework** | No web framework — custom CLI application |
| **Language** | Python 3.12+ (`requires-python = ">=3.12"` in pyproject.toml) |
| **Runtime** | CPython |
| **Platform** | CLI (`python -m llmitm_v2`) |
| **Dependencies (from pyproject.toml)** | pydantic>=2.0, pydantic-settings>=2.0, neo4j>=5.0, httpx>=0.25.0, anthropic>=0.20.0, mitmproxy>=10.0, sentence-transformers>=2.2.0 |
| **Dev deps** | pytest>=7.0, ruff>=0.1.0, black>=23.0, mypy>=1.0 |

### 4.2 Architecture Type (from reading orchestrator.py + agents.py)

| Aspect | Observed from Code |
|--------|-------------------|
| **Pattern** | Deterministic pipeline with LLM used only at "compile time" |
| **Core loop** | `Orchestrator.run()` → `_try_warm_start()` or `_compile()` → `_execute()` → optional `_repair()` |
| **LLM usage** | Two agent classes: `SimpleAgent` (structured output, no tools) and `ProgrammaticAgent` (code_execution sandbox + tool calling). Both use Anthropic SDK directly. |
| **Storage** | Neo4j via `GraphRepository` (optional — graceful fallback on import failure) |
| **Deployment** | Docker Compose: 7 services (neo4j, 3 vulnerable web apps, 2 databases, mitmproxy) |

```
┌─────────────────────────────────────────────────────────┐
│              CLI (__main__.py → main())                   │
│  Loads Settings, wires budget, connects Neo4j            │
├─────────────────────────────────────────────────────────┤
│              Orchestrator.run()                           │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │ agents.py    │  │ handlers/  │  │ graph_repository│  │
│  │ 2 agents     │  │ 3 handlers │  │ .py (492 LOC)   │  │
│  │ (Anthropic   │  │ (HTTP,     │  │ All Neo4j       │  │
│  │  SDK)        │  │  Shell,    │  │ queries         │  │
│  │              │  │  Regex)    │  │                 │  │
│  └──────┬───────┘  └─────┬──────┘  └────────┬────────┘  │
│         │                │                   │           │
│  ┌──────▼────────────────▼───────────────────▼────────┐  │
│  │ tools/ (4 recon + 5 exploit + graph)               │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │ models/ (18 Pydantic models — used by all layers)  │  │
│  └────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│ External: Neo4j 5 │ mitmproxy │ httpx │ Anthropic API  │
└─────────────────────────────────────────────────────────┘
```

### 4.3 Entry Points (from Makefile + __main__.py)

| Entry Point | Command | What It Actually Does (from reading code) |
|-------------|---------|------------------------------------------|
| Main CLI | `python -m llmitm_v2` | Loads Settings → connect Neo4j → setup_schema → create Orchestrator → file or live mode → print results |
| Test | `make test` → `pytest` | Runs 8 test files (testpaths=["tests"] from pyproject.toml) |
| Schema | `make schema` | Runs `setup_schema.py` — creates UNIQUE constraints + vector indexes |
| Run targets | `make run` / `run-nodegoat` / `run-dvwa` | Sets TARGET_PROFILE + TRAFFIC_FILE env vars, then runs CLI |
| Snapshot | `make snapshot NAME=x` | Runs `scripts/export-snapshot.sh` (neo4j-admin dump + APOC export) |
| Seed | `make seed` | Runs `scripts/seed-demo-graph.py` (inserts known-good IDOR ActionGraph) |
| Break/Fix | `make break-graph` | Runs `scripts/break-graph.sh` (corrupts GET→PATCH on /api/Users steps) |

---

## 5. Codebase Scale

### 5.1 Scale Metrics (from `wc -l`)

| Metric | Counted Value |
|--------|--------------|
| Total Python LOC | 4,910 (all .py files including scripts) |
| Source LOC (`llmitm_v2/`) | 3,618 |
| Test LOC (`tests/`) | 1,093 |
| Script LOC (`scripts/`) | 199 |
| Test-to-source ratio | 30.2% |
| Python files | 47 (37 source + 9 test + 1 script) |
| Classes (from tags.md) | 26 source classes + 10 test classes |
| Functions (from tags.md) | 58 standalone functions |
| Methods (from tags.md) | 48 methods |
| Test cases | 119 passing, 1 skipped |

### 5.2 File Size Distribution (from `wc -l`)

| Category | Count | Files |
|----------|-------|-------|
| Small (<100 LOC) | 22 | All `__init__.py`, `base.py` (14), `constants.py` (39), `config.py` (49), `step.py` (34), etc. |
| Medium (100-300 LOC) | 20 | `fingerprinter.py` (184), `debug_logger.py` (240), `exploit_tools.py` (244), all test files |
| Large (300-500 LOC) | 4 | `orchestrator.py` (343), `recon_tools.py` (323), `agents.py` (396), `graph_repository.py` (492) |
| Very Large (500+) | 0 | None |

### 5.3 Largest Files

| File | LOC | What It Contains (from reading) |
|------|-----|--------------------------------|
| `repository/graph_repository.py` | 492 | 9 public methods, each wrapping Cypher in `session.execute_read/write` managed transactions |
| `orchestrator/agents.py` | 396 | 2 agent classes, 2 factory functions, 2 system prompts, token budget enforcement, content sanitization |
| `orchestrator/orchestrator.py` | 343 | Orchestrator class: run(), _try_warm_start(), _compile(), _execute(), _handle_step_failure(), _repair(), _interpolate_params(), attack_plan_to_action_graph() |
| `tools/recon_tools.py` | 323 | 4 tool functions + 6 helper functions, all reading .mitm files via FlowReader |
| `tools/exploit_tools.py` | 244 | 5 step generator functions + 4 helper functions, all producing List[Step] |

No file exceeds 500 LOC. The largest is the repository, which is justified by containing all Neo4j queries in one place (Repository pattern).

---

## 6. Project Organization

### 6.1 Separation of Concerns (assessed from actual imports)

| Concern | Where It Lives | Boundary Clear? | Evidence |
|---------|---------------|-----------------|----------|
| Data models | `models/` | Yes | Models import only from `constants` and each other. No external deps. |
| LLM interaction | `orchestrator/agents.py` | Yes | Only file importing `anthropic` SDK (besides `graph_tools.py` for `@beta_tool`) |
| Control flow | `orchestrator/orchestrator.py` | Yes | Imports handlers, agents, tools, repo — orchestrates all |
| Step execution | `handlers/` | Yes | Each handler imports only models + stdlib (`httpx`, `subprocess`, `re`) |
| Data persistence | `repository/` | Yes | Only place with Neo4j Cypher. Graceful fallback if driver not installed. |
| Tool definitions | `tools/` | Yes | Each tool file exports dict of schemas/handlers, consumed by agents |
| Configuration | Root `.py` files | Mostly | `config.py` is clean. `target_profiles.py` mixes data + logic. `constants.py` is clean. |
| Traffic capture | `capture/` | Partial | `addon.py` is mitmproxy-specific. `launcher.py` imports both `httpx` and `mitmproxy.io`. |

### 6.2 Public API Surface

This is a CLI application, not a library. The only public interface is:

```
python -m llmitm_v2   # Configured entirely via env vars (see config.py Settings)
```

All `__init__.py` files re-export public names, but these are for internal package use, not external consumption.

### 6.3 Configuration Organization

| Config Type | Location | How It Works (from reading code) |
|-------------|----------|----------------------------------|
| Runtime settings | `config.py` | `Settings(BaseSettings)` — loads from `.env` or env vars. 20+ fields with defaults. |
| Target profiles | `target_profiles.py` | `TARGET_PROFILES` dict of 3 hardcoded TargetProfile instances. Selected by `TARGET_PROFILE` env var. |
| Docker services | `docker-compose.yml` | 7 services: neo4j (APOC+vector), juiceshop, nodegoat, mongo, dvwa, mysql, mitmproxy |
| DB schema | `repository/setup_schema.py` | Idempotent Cypher — 3 UNIQUE constraints + 2 vector indexes (384-dim, cosine) |
| Build/run | `Makefile` | 18 phony targets. `PYTHON` var points to `.venv/bin/python3` |

---

## Summary

### Project Profile

| Aspect | Assessment | Evidence |
|--------|-----------|---------|
| **Size** | Small (3,618 source LOC, 47 Python files) | `wc -l` totals |
| **Complexity** | High relative to size | LLM agents, Neo4j graph DB, mitmproxy capture, multi-target, self-repair loop |
| **Organization** | Well-organized | Clean layer separation, consistent naming, no circular imports |
| **Maturity** | Hackathon prototype (v0.1.0) | Working E2E on 3 targets, but dead code present |

### Structural Health

| Aspect | Status | Evidence from Code |
|--------|--------|-------------------|
| Directory organization | Strong | Layer-based grouping, no misplaced files |
| Naming consistency | Strong | All classes PascalCase, all functions snake_case, all factories `create_*` |
| Separation of concerns | Strong | Import graph is strictly layered, no circular deps |
| Test organization | Strong | 1:1 mapping between source modules and test files |

### Findings from Code Reading

1. **2 unimplemented StepTypes**: `constants.py` defines `JSON_EXTRACT` and `RESPONSE_COMPARE` in the `StepType` enum, but `registry.py` only maps 3 types to handlers. Calling `get_handler()` with these raises `ValueError`.
2. **Dead `hooks/` module**: Contains only a docstring noting `ApprovalHook` was removed during Strands migration.
3. **`CriticFeedback` unused**: Defined in `models/critic.py` but the orchestrator only uses `RepairDiagnosis`. The compile loop uses `AttackPlan` for critic output, not `CriticFeedback`.
4. **Runtime artifacts in git**: `capture/flows.json` (3.1M) and `llmitm_v2/tmp/` contain runtime data.
5. **Legacy file**: `demo/juice_shop_traffic.txt` is not referenced by any code (config uses `.mitm` files).
6. **`graph_tools.py` uses `@beta_tool`**: Only remaining use of Anthropic beta tool decorator. Not used in main agent pipeline (ProgrammaticAgent uses TOOL_SCHEMAS/TOOL_HANDLERS dicts instead).
7. **`capture/__init__.py` exports nothing**: Unlike other subpackages that re-export their public names, `capture/` has an empty init. Callers import directly from submodules.
8. **Skill guides loaded but not injected**: `load_skill_guides()` function exists in `agents.py` and reads 4 markdown files, but the system prompt replaces `{skill_guides}` with empty string.

### Memory File Drift (observed vs documented)

| Item | Memory Claim | Actual Code | Severity |
|------|-------------|-------------|----------|
| `MAX_CRITIC_ITERATIONS` constant | "reduced 5→3" | Constant still 5 in `constants.py:35`, but `config.py:29` defaults to 3. Orchestrator reads from Settings, not the constant. **Constant is dead code.** | Medium — misleading but runtime correct |
| Makefile targets | `techContext.md` lists only 6 targets | 18 targets exist (multi-target support added later) | Medium — stale docs |
| StepType orphans | Not mentioned anywhere | `JSON_EXTRACT` and `RESPONSE_COMPARE` defined but have no handlers | Medium — undocumented dead code |
| `hooks/` module | projectProgress.md notes ApprovalHook removed | Empty directory still exists | Low — should be in tech debt |

### Recommendations

- Delete `hooks/` directory (dead code)
- Remove `capture/flows.json` and `llmitm_v2/tmp/` from version control (add to `.gitignore`)
- Remove `demo/juice_shop_traffic.txt` (unreferenced)
- Either implement `JSON_EXTRACT`/`RESPONSE_COMPARE` handlers or remove from `StepType` enum
- Remove `CriticFeedback` from `models/critic.py` if truly unused
- Add re-exports to `capture/__init__.py` for consistency with other subpackages
