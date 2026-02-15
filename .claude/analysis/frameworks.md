# Framework Configuration Analysis

## 1. Framework Identity

### 1.1 Primary Framework

| Aspect | Details |
|--------|---------|
| **Name** | Pydantic v2 + pydantic-settings |
| **Version** | `pydantic>=2.0`, `pydantic-settings>=2.0` |
| **Type** | Data validation / configuration framework (CLI agent — no web framework) |
| **Documentation** | https://docs.pydantic.dev/latest/ |

Pydantic is the structural backbone: every model, DTO, LLM output schema, and config setting is a Pydantic `BaseModel` or `BaseSettings`. It serves triple duty: validation, type safety, and contract enforcement at every boundary.

### 1.2 Secondary Frameworks

| Framework | Purpose | Version |
|-----------|---------|---------|
| **Anthropic Python SDK** | LLM integration — structured output, code execution sandbox, tool calling | `>=0.20.0` |
| **Neo4j Python Driver** | Graph database access via Cypher queries | `>=5.0` |
| **mitmproxy** | HTTP traffic interception and replay | `>=10.0` |
| **httpx** | Synchronous HTTP client for step execution | `>=0.25.0` |
| **sentence-transformers** | Embedding generation for fingerprint similarity | `>=2.2.0` |
| **pytest** | Test framework | `>=7.0` (dev) |
| **ruff** | Linter and formatter | `>=0.1.0` (dev) |
| **black** | Code formatter | `>=23.0` (dev) |
| **mypy** | Static type checker | `>=1.0` (dev) |
| **setuptools** | Build backend | `>=65.0` |

---

## 2. Configuration

### 2.1 Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `pyproject.toml` | Build system, dependencies, tool configs | TOML |
| `docker-compose.yml` | Service orchestration (Neo4j, targets, mitmproxy) | YAML |
| `Makefile` | Task runner (18 targets) | Make |
| `llmitm_v2/config.py` | Runtime settings via `BaseSettings` | Python |
| `.env` | Environment variable overrides (optional) | dotenv |

### 2.2 Configuration Details

#### `pyproject.toml`

| Setting | Value | Purpose | Default |
|---------|-------|---------|---------|
| `requires-python` | `>=3.12` | Minimum Python version | N/A |
| `build-backend` | `setuptools.build_meta` | PEP 517 build backend | N/A |
| `tool.ruff.line-length` | `100` | Max line length | 88 |
| `tool.ruff.target-version` | `py312` | Python target for linting rules | py38 |
| `tool.ruff.select` | `E, W, F, I, B, C4` | Enabled rule sets (pycodestyle, pyflakes, isort, bugbear, comprehensions) | `E, W, F` |
| `tool.ruff.ignore` | `E501, W291` | Suppressed rules (handled by formatter) | none |
| `tool.pytest.testpaths` | `["tests"]` | Test discovery root | `.` |
| `tool.pytest.addopts` | `-v --tb=short` | Default pytest flags | none |
| `tool.mypy.disallow_untyped_defs` | `false` | Gradual typing mode | false |

#### `llmitm_v2/config.py` (Settings)

| Setting | Value | Purpose | Default |
|---------|-------|---------|---------|
| `neo4j_uri` | (required) | Neo4j connection string | none |
| `neo4j_username` | `neo4j` | Neo4j auth username | `neo4j` |
| `neo4j_password` | (required) | Neo4j auth password | none |
| `neo4j_database` | `neo4j` | Neo4j database name | `neo4j` |
| `anthropic_api_key` | (required) | Anthropic API key | none |
| `model_id` | `claude-sonnet-4-5-20250929` | Default LLM model | N/A |
| `target_url` | `http://localhost:3000` | Target app base URL | `http://localhost:3000` |
| `max_critic_iterations` | `3` | Max actor/critic loop rounds | N/A |
| `similarity_threshold` | `0.85` | Fingerprint similarity cutoff | N/A |
| `max_token_budget` | `50_000` | Cumulative token limit per run | N/A |
| `embedding_model` | `all-MiniLM-L6-v2` | Sentence transformer model | N/A |
| `embedding_dimensions` | `384` | Vector dimensions | N/A |
| `capture_mode` | `file` | `file` or `live` mode | `file` |
| `traffic_file` | `demo/juice_shop.mitm` | Path to .mitm capture | N/A |
| `target_profile` | `juice_shop` | Target profile name | `juice_shop` |
| `log_level` | `INFO` | Python logging level | `INFO` |

#### `docker-compose.yml`

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `neo4j` | `neo4j:5-community` | 7474, 7687 | Graph database with APOC plugin |
| `juiceshop` | `bkimminich/juice-shop:latest` | 3000 | OWASP Juice Shop target |
| `nodegoat` | `owasp-nodegoat:local` | 4000 | OWASP NodeGoat target (requires local build) |
| `dvwa` | `vulnerables/web-dvwa:latest` | 8081 | DVWA target |
| `mongo` | `mongo:4.4` | — | MongoDB for NodeGoat |
| `mysql` | `mysql:5.7` | — | MySQL for DVWA |
| `mitmproxy` | `mitmproxy/mitmproxy:latest` | 8080 | Reverse proxy to Juice Shop |

---

## 3. Framework Patterns

### 3.1 Architecture Pattern

| Aspect | Details |
|--------|---------|
| **Pattern Name** | Graph-Native Custom Logic Agent (layered architecture) |
| **Implementation** | Python orchestrator owns all control flow. Neo4j stores all state. LLM is a stateless compiler invoked only for novel fingerprints and repair. 95% deterministic graph traversal. |
| **Deviations** | No web framework — this is a CLI agent. No MVC/component pattern. Uses Repository pattern for data access, Strategy pattern for context assembly, Handler Registry for step dispatch. |

### 3.2 Rendering Strategy

| Aspect | Details |
|--------|---------|
| **Type** | N/A — CLI application, no UI rendering |
| **Mechanism** | Python `logging` module for console output |
| **Data Fetching** | Neo4j queries via `GraphRepository`, HTTP requests via `httpx.Client` |

### 3.3 Routing

| Aspect | Details |
|--------|---------|
| **Type** | N/A — no HTTP routing (CLI app) |
| **Definition** | Single entry point: `python -m llmitm_v2` → `__main__.py:main()` |
| **Dynamic Routes** | Two execution modes selected by `CAPTURE_MODE` env var: `file` (offline) or `live` (recon agent) |

### 3.4 Framework Conventions

| Convention | Usage | Location |
|------------|-------|----------|
| Pydantic `BaseModel` for all DTOs | Every data transfer object is a Pydantic model | `llmitm_v2/models/` |
| Pydantic `BaseSettings` for config | All env vars loaded via `Settings` class | `llmitm_v2/config.py` |
| `model_validator` / `field_validator` | Auto-generate IDs, compute hashes, sanitize LLM output | `models/fingerprint.py`, `models/recon.py` |
| Pydantic `output_format=` with Anthropic SDK | Grammar-constrained LLM decoding ensures valid schema | `orchestrator/agents.py` |
| ABC + concrete implementations | `StepHandler` ABC with HTTP/Shell/Regex handlers | `handlers/base.py`, `handlers/*.py` |
| `create_*` factory functions | Construct configured agents and tools | `orchestrator/agents.py`, `tools/graph_tools.py` |

### 3.5 Special Features

| Feature | Enabled | Configuration |
|---------|---------|---------------|
| Anthropic code_execution sandbox | Yes | Beta headers: `code-execution-2025-08-25`, `advanced-tool-use-2025-11-20` |
| Anthropic grammar-constrained decoding | Yes | `output_format=PydanticModel` on `messages.parse()` |
| Neo4j APOC plugin | Yes | `NEO4J_PLUGINS: '["apoc"]'` in docker-compose |
| Neo4j vector indexes (HNSW) | Yes | 384-dim cosine similarity for fingerprint matching |
| Token budget enforcement | Yes | Module-level counter in `agents.py`, `RuntimeError` on exceed |
| Debug logging (opt-in) | Yes | `LLMITM_DEBUG=1` enables per-call JSON traces |

---

## 4. Build System

### 4.1 Build Tool

| Aspect | Details |
|--------|---------|
| **Tool** | setuptools |
| **Version** | `>=65.0` |
| **Config File** | `pyproject.toml` |

### 4.2 Build Commands

| Command | Purpose | Output |
|---------|---------|--------|
| `pip install -e .` | Editable install | Package installed in dev mode |
| `make test` | Run pytest | Test results |
| `make run` | Run file mode (Juice Shop default) | Orchestration output |
| `make run-live` | Run live mode with recon agent | Orchestration output |
| `make run-nodegoat` | Run file mode against NodeGoat | Orchestration output |
| `make run-dvwa` | Run file mode against DVWA | Orchestration output |
| `make up` / `make down` | Docker Compose lifecycle | Services started/stopped |
| `make schema` | Initialize Neo4j constraints + indexes | Schema created |
| `make reset` | Wipe Neo4j + recreate schema | Clean database |
| `make seed` | Insert known-good IDOR ActionGraph | Demo data |
| `make snapshot NAME=x` | Binary dump + APOC export | Backup in `snapshots/` |
| `make restore NAME=x` | Binary load + schema recreate | Restored database |
| `make break-graph` | Corrupt graph for repair demo | Broken ActionGraph |
| `make fix-graph` | Reverse corruption | Fixed ActionGraph |

### 4.3 Compiler Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| Python target | 3.12 | Minimum Python version (`requires-python`, ruff, black, mypy) |
| mypy `disallow_untyped_defs` | `false` | Gradual typing — not enforcing full annotations |
| mypy `warn_return_any` | `true` | Flag `Any` return types |

### 4.4 Build Optimizations

| Optimization | Enabled | Configuration |
|--------------|---------|---------------|
| Editable install | Yes | `pip install -e .` for development |
| No bundling/minification | N/A | Pure Python — no compilation step |

---

## 5. Environment Configuration

### 5.1 Environment Modes

| Mode | Purpose | Activation |
|------|---------|------------|
| Development | Local Docker Compose + .venv | `make up` + `pip install -e .` |
| File mode | Offline analysis of .mitm captures | `CAPTURE_MODE=file` (default) |
| Live mode | Active recon against running target | `CAPTURE_MODE=live` |
| Test | Unit + integration tests | `make test` |

### 5.2 Environment-Specific Settings

| Setting | Development | Live | Test |
|---------|-------------|------|------|
| `NEO4J_URI` | `bolt://localhost:7687` | Same | Tests skip if unavailable |
| `TARGET_URL` | Auto-resolved from profile | Same | Not needed |
| `CAPTURE_MODE` | `file` | `live` | Not used |
| `ANTHROPIC_API_KEY` | Real key | Real key | `dummy` (unit tests don't call API) |
| `MAX_TOKEN_BUDGET` | `50_000` | `150_000` (techContext says this) | Not used |

---

## Summary

### Framework Stack

```
┌─────────────────────────────────────────┐
│           CLI Entry Point               │
│       python -m llmitm_v2               │
├─────────────────────────────────────────┤
│         Orchestrator Layer              │
│  (custom control flow, no framework)    │
├──────────┬──────────┬───────────────────┤
│ Anthropic│  Neo4j   │   mitmproxy       │
│   SDK    │  Driver  │   (subprocess)    │
│ (LLM)   │  (graph) │   (traffic)       │
├──────────┴──────────┴───────────────────┤
│         Pydantic v2 (everywhere)        │
│  Models · Config · LLM schemas · DTOs   │
├─────────────────────────────────────────┤
│       httpx · sentence-transformers     │
│      (HTTP client)  (embeddings)        │
├─────────────────────────────────────────┤
│    Docker Compose (Neo4j + targets)     │
└─────────────────────────────────────────┘
```

### Configuration Health

| Aspect | Status | Notes |
|--------|--------|-------|
| Security defaults | Needs attention | Docker Compose uses hardcoded Neo4j/MySQL passwords (`password`, `dvwa`) |
| Performance | Good | Token budget enforcement, max_iterations caps, warm start zero-cost path |
| DX | Good | Makefile with 18 targets, `.env` support, editable install |
| Type safety | Good | Pydantic enforces all boundaries; mypy in gradual mode |
| Test coverage | Good | 119 tests, no mocks, real inputs/outputs, integration tests skip gracefully |

### Recommendations

- [ ] Move hardcoded Docker credentials to `.env` template (security hygiene)
- [ ] Add `ruff check` and `mypy` to `make test` or a `make lint` target
- [ ] Consider `pyproject.toml` `[project.scripts]` entry point instead of `__main__.py` for cleaner CLI invocation
- [ ] Pin exact dependency versions in a lock file for reproducible builds
