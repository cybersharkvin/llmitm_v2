# Major Outputs Analysis

## 1. UI Rendering

This is a CLI application with no web UI. All user-facing output is via Python `logging` (INFO level) and `print()`.

### 1.1 Pages/Views

N/A — CLI tool, no pages.

### 1.2 Console Output

| Output | Location | Trigger | Content |
|--------|----------|---------|---------|
| Schema constraints | `repository/setup_schema.py:25-47` | `setup_schema(quiet=False)` | Checkmark per constraint created (Fingerprint hash, ActionGraph id, Finding id) |
| Schema vector indexes | `repository/setup_schema.py:50-77` | `setup_schema(quiet=False)` | Checkmark per vector index (Fingerprint embedding, Finding embedding) |
| Schema complete | `repository/setup_schema.py:79` | End of setup | `✅ Schema setup complete` |
| Token usage | `orchestrator/agents.py:38-41` | Every Anthropic API call | `API call: model=X input=N output=N cumulative=N/N` |
| Warm start match | `__main__.py:65` | Fingerprint hash found in Neo4j | First 12 chars of hash |
| Known but no graph | `__main__.py:68` | Fingerprint exists, no ActionGraph | Status message |
| No fingerprint | `__main__.py:71` | `quick_fingerprint()` returns None | Status message |
| Fingerprint details | `__main__.py:114-118` | After orchestration | tech_stack, auth_model, endpoint_pattern |
| Run results | `__main__.py:121-128` | After orchestration | Path (cold/warm/repair), compiled, repaired, success, steps, findings |
| Fingerprint failure | `capture/launcher.py:96` | `fingerprint_from_mitm()` exception | Warning with stack trace |

**UI Summary**: User runs `python -m llmitm_v2` or `make run`. They see logging output showing the execution path (cold/warm/repair), per-call token consumption, and final results (success boolean, step count, finding count). No interactive input during execution.

---

## 2. File Generation

### 2.1 Runtime Generated Files

| File | Path Pattern | Trigger | Format | Purpose |
|------|-------------|---------|--------|---------|
| API call log | `debug_logs/<timestamp>/call_NNN.json` | Each Anthropic API call | JSON | Agent reasoning trace: model, tokens, content blocks, tool calls |
| Event log | `debug_logs/<timestamp>/event_NNN_<type>.json` | Orchestrator milestones | JSON | Decision trace: compile_iter, critic_result, step_result, failure |
| Run summary | `debug_logs/<timestamp>/run_summary.json` | End of run | JSON | Aggregate stats: total tokens, path, success, all calls/events |
| HTTP response | `llmitm_v2/tmp/<name>` | `step.output_file` set on HTTP step | Plain text | Raw response body for downstream regex extraction |
| Captured flows | `capture/flows.json` | Every HTTP flow through mitmproxy addon | JSON array | All intercepted request/response pairs (Docker mode) |

**Debug logging** is opt-in via `DEBUG_LOGGING=true` env var (`debug_logger.py:96-108`). Creates timestamped directory. Files 1-3 above only written when enabled. Files 4-5 are always written when their triggers occur.

### 2.2 Build Artifacts

None — no build step beyond `pip install -e .`.

### 2.3 Static Assets

None served to users.

---

## 3. API Responses

N/A — this is a CLI tool, not a server. No endpoints.

---

## 4. Side Effects

### 4.1 Database Writes (Neo4j)

| Operation | Location | Creates/Updates | Trigger |
|-----------|----------|-----------------|---------|
| Save fingerprint | `graph_repository.py:27-56` | MERGE `(:Fingerprint)` by hash; sets tech_stack, auth_model, endpoint_pattern, security_signals, embedding | Every `orchestrator.run()` call |
| Save action graph | `graph_repository.py:116-207` | CREATE `(:ActionGraph)` + `(:Step)` chain + `[:TRIGGERS]`, `[:HAS_STEP]`, `[:STARTS_WITH]`, `[:NEXT]` relationships | After successful `_compile()` |
| Save finding | `graph_repository.py:265-303` | CREATE `(:Finding)` + `[:PRODUCED_BY]` | OBSERVE-phase step matches success_criteria |
| Increment count | `graph_repository.py:423-449` | SET `times_executed += 1`, optionally `times_succeeded += 1` | After every execution |
| Repair step chain | `graph_repository.py:305-421` | DELETE old steps, CREATE new `(:Step)` nodes + `[:REPAIRED_TO]` edges, rewire `[:NEXT]` | Systemic failure triggers `_repair()` |
| Schema setup | `setup_schema.py:12-79` | CREATE CONSTRAINT (3x), CREATE VECTOR INDEX (2x) | CLI startup or `make schema` |

### 4.2 External API Calls (Outbound)

| Service | Location | Method | Trigger | Data Sent |
|---------|----------|--------|---------|-----------|
| Anthropic (Critic) | `agents.py:171-186` | `client.messages.parse()` | Each critic iteration in `_compile()` | System prompt + AttackPlan JSON → returns refined AttackPlan |
| Anthropic (Recon) | `agents.py:265-342` | `client.beta.messages.create()` | Recon agent in `_compile()` | System prompt + context + tool results; code_execution sandbox + 4 recon tools |

**Budget guard** (`agents.py:26-49`): Cumulative token counter. Raises `RuntimeError` at `_max_token_budget` (default 150K).

### 4.3 HTTP Requests to Target

| Request | Location | Trigger | Details |
|---------|----------|---------|---------|
| Fingerprint probes | `capture/launcher.py:20-56` | Live mode startup | 3 GETs to `/`, `/api/`, `/rest/` with `verify=False` |
| Step execution | `handlers/http_request_handler.py:17-71` | Each HTTP_REQUEST step | Method/URL/headers/body from step params; cookies + auth from context; form-encoded default |

### 4.4 Subprocess Execution

| Command | Location | Trigger | Details |
|---------|----------|---------|---------|
| Shell commands | `handlers/shell_command_handler.py:15-39` | Each SHELL_COMMAND step | `subprocess.run(shell=True)`, timeout default 120s, merged env vars |

### 4.5 Notifications

None — no email, SMS, push, or webhooks.

### 4.6 Logging

All via Python `logging` at INFO level. Key log points documented in Section 1.2.

---

## 5. Downloads/Exports

N/A — no user downloads or data exports. Persistent output goes to Neo4j; diagnostic output to debug log files.

---

## Summary

### Output Counts

| Category | Count | User-Facing |
|----------|-------|-------------|
| Console log messages | ~10 distinct | Yes |
| Generated file types | 5 | No (debug/internal) |
| API Endpoints | 0 | N/A |
| Database write operations | 6 | No |
| External API integrations | 1 (Anthropic, 2 agent types) | No |
| HTTP request types | 2 (probes + steps) | No |
| Subprocess types | 1 | No |
| Downloads/Exports | 0 | N/A |
| **TOTAL** | **25** | **~10** |

### Output Flow

```
                         ┌─────────────┐
                         │  CLI Entry   │
                         │ __main__.py  │
                         └──────┬──────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                  ▼
     ┌────────────┐    ┌──────────────┐   ┌───────────────┐
     │ Console    │    │ Orchestrator │   │ Fingerprinter │
     │ (logging)  │    │              │   │ (HTTP probes) │
     └────────────┘    └──────┬───────┘   └───────────────┘
                              │
           ┌──────────┬───────┼────────┬──────────┐
           ▼          ▼       ▼        ▼          ▼
     ┌──────────┐ ┌───────┐ ┌─────┐ ┌──────┐ ┌────────┐
     │ Anthropic│ │ Neo4j │ │HTTP │ │Shell │ │ Debug  │
     │ API      │ │ Graph │ │Reqs │ │Cmds  │ │ Logs   │
     └──────────┘ └───────┘ └─────┘ └──────┘ └────────┘
```

### Failure Modes

| Output | Failure Scenario | Handling | User Impact |
|--------|------------------|----------|-------------|
| Neo4j writes | Connection lost | Exception propagates to CLI | Run aborts with stack trace |
| Anthropic API | Token budget exhausted | `RuntimeError` raised (`agents.py:48`) | Run aborts; partial results lost |
| Anthropic API | Rate limit / 5xx | Exception propagates | Run aborts |
| HTTP to target | Target unreachable | `StepResult` with stderr | Step fails; triggers failure classifier |
| Shell command | Timeout | `TimeoutExpired` caught (`shell_command_handler.py:35`) | stderr set to timeout message; step fails |
| Debug log writes | Disk full / permissions | Silent failure (no try/except) | Debug logs missing but run continues |
| Addon flows.json | Path missing | `try/except pass` (`addon.py:41`) | Silently skipped |

### Idempotency

| Operation | Idempotent? | Notes |
|-----------|-------------|-------|
| `save_fingerprint()` | Yes | Uses MERGE by hash |
| `save_action_graph()` | No | CREATE always; duplicates possible |
| `save_finding()` | No | CREATE always |
| `increment_execution_count()` | No | Monotonically increasing |
| `setup_schema()` | Yes | IF NOT EXISTS on all constraints/indexes |
| `repair_step_chain()` | No | Destructive: deletes old steps |
