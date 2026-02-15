# Third-Party Libraries Analysis

## 1. Dependency Inventory

### 1.1 Runtime Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| pydantic | 2.11.10 | Schema validation for all DTOs, LLM structured output, and Neo4j serialization |
| pydantic-settings | 2.12.0 | Environment-variable-backed configuration via `Settings(BaseSettings)` |
| neo4j | 6.1.0 | Python driver for Neo4j graph database (managed transactions, connection pooling) |
| httpx | 0.28.1 | Synchronous HTTP client for target interaction in step handlers and fingerprinting |
| sentence-transformers | 5.2.2 | Embedding model (`all-MiniLM-L6-v2`) for fingerprint vector similarity search |
| anthropic | 0.79.0 | LLM SDK for structured output, code execution sandbox, and programmatic tool calling |
| mitmproxy | 12.2.1 | HTTP traffic interception, capture file parsing via `FlowReader`, and addon framework |

### 1.2 Development Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| pytest | 9.0.2 | Test framework for unit and integration tests |
| pytest-cov | (declared, >=4.0) | Coverage reporting for pytest |
| ruff | (declared, >=0.1.0) | Linting and formatting |
| black | (declared, >=23.0) | Code formatting (redundant with ruff) |
| mypy | (declared, >=1.0) | Static type checking |
| ipython | (declared, >=8.0) | Interactive debugging shell |

### 1.3 Notable Transitive Dependencies

| Library | Version | Required By | Used Directly? |
|---------|---------|-------------|----------------|
| Flask | 3.1.2 | mitmproxy | No — never imported in source |
| httpx-sse | 0.4.3 | anthropic | No |
| pydantic-core | 2.33.2 | pydantic | No (internal) |
| mitmproxy_rs | 0.12.9 | mitmproxy | No (Rust bindings) |
| setuptools | 82.0.0 | build system | No |
| torch | (installed) | sentence-transformers | No — only via SentenceTransformer API |
| numpy | (installed) | sentence-transformers, torch | No |
| transformers | (installed) | sentence-transformers | No |

---

## 2. Usage Analysis

### 2.1 Most Used Libraries

| Library | Import Count | Files | Criticality |
|---------|-------------|-------|-------------|
| pydantic | 9 | All model files, debug_logger, target_profiles | High — every data boundary |
| pytest | 8 | All test files | High (dev only) |
| neo4j | 4 | __main__, setup_schema, graph_repository, test_graph_repository | High — persistence layer |
| mitmproxy | 3 | recon_tools, addon, launcher | High — traffic capture/parsing |
| anthropic | 2 | agents, graph_tools | High — LLM compilation/repair |
| httpx | 2 | http_request_handler, launcher | High — all HTTP execution |
| pydantic-settings | 1 | config.py | Medium — configuration |
| sentence-transformers | 1 | graph_tools.py (lazy import) | Low — only vector search |

### 2.2 Unused Dependencies

| Library | Status | Recommendation |
|---------|--------|----------------|
| black | Declared in dev deps; ruff handles formatting | Remove — redundant with ruff |
| pytest-cov | Declared, not confirmed installed | Keep — useful for coverage runs |
| mypy | Declared; `disallow_untyped_defs = false` in config | Keep — incremental adoption |
| ipython | Declared; convenience only | Keep — developer ergonomics |

### 2.3 Implicit Dependencies

| Library | Pulled In By | Used Directly? |
|---------|--------------|----------------|
| Flask | mitmproxy | No |
| torch | sentence-transformers | No |
| numpy | sentence-transformers | No |
| transformers | sentence-transformers | No |
| cryptography | mitmproxy | No |

---

## 3. Import Locations

### anthropic

| Import | Location | Purpose |
|--------|----------|---------|
| `import anthropic` | `orchestrator/agents.py:15` | Create `Anthropic` client; `messages.parse()` and `beta.messages.create()` |
| `from anthropic import beta_tool` | `tools/graph_tools.py:9` | `@beta_tool` decorator for embedding-based graph queries |

### pydantic

| Import | Location | Purpose |
|--------|----------|---------|
| `from pydantic import BaseModel, Field` | `models/action_graph.py:6` | ActionGraph schema |
| `from pydantic import BaseModel, Field` | `models/finding.py:6` | Finding schema |
| `from pydantic import BaseModel, Field` | `models/context.py:5` | ExecutionContext, StepResult, ExecutionResult |
| `from pydantic import BaseModel, ConfigDict, Field` | `models/critic.py:5` | CriticFeedback, RepairDiagnosis |
| `from pydantic import BaseModel, Field` | `models/fingerprint.py:6` | Fingerprint with hash computation |
| `from pydantic import BaseModel, ConfigDict, Field` | `models/step.py:5` | Step with CAMRO phase |
| `from pydantic import BaseModel, Field, field_validator` | `models/recon.py:11` | AttackPlan with LLM output sanitization |
| `from pydantic import BaseModel, Field` | `debug_logger.py:13` | Log entry models |
| `from pydantic import BaseModel` | `target_profiles.py:9` | TargetCredentials, TargetProfile |

### pydantic-settings

| Import | Location | Purpose |
|--------|----------|---------|
| `from pydantic_settings import BaseSettings, SettingsConfigDict` | `config.py:3` | `Settings` class with env-var binding |

### neo4j

| Import | Location | Purpose |
|--------|----------|---------|
| `from neo4j import GraphDatabase` | `__main__.py:8` | Create driver singleton for CLI entry |
| `from neo4j import GraphDatabase` | `repository/setup_schema.py:5` | Create driver for schema setup |
| `from neo4j import Driver, Session` | `repository/graph_repository.py:6` | Type hints + managed transactions |
| `from neo4j import GraphDatabase` | `tests/test_graph_repository.py:16` | Integration test driver (skip if unavailable) |

### httpx

| Import | Location | Purpose |
|--------|----------|---------|
| `import httpx` | `handlers/http_request_handler.py:7` | Execute HTTP steps (GET/POST with cookies, headers, redirects) |
| `import httpx` | `capture/launcher.py:11` | `quick_fingerprint()` sends 3 probe requests |

### mitmproxy

| Import | Location | Purpose |
|--------|----------|---------|
| `from mitmproxy.io import FlowReader` | `tools/recon_tools.py:11` | Parse .mitm capture files for recon analysis |
| `from mitmproxy import http` | `capture/addon.py:9` | HTTP flow type for capture addon |
| `from mitmproxy.io import FlowReader` | `capture/launcher.py:12` | Parse .mitm files for offline fingerprinting |

### sentence-transformers

| Import | Location | Purpose |
|--------|----------|---------|
| `from sentence_transformers import SentenceTransformer` | `tools/graph_tools.py:31` | Lazy-loaded `all-MiniLM-L6-v2` for fingerprint vector similarity |

---

## 4. Library Categories

### Core/Framework

| Library | Purpose | Alternatives |
|---------|---------|--------------|
| pydantic | Schema validation at every boundary | dataclasses + manual validation, attrs |
| pydantic-settings | Env-var config | python-decouple, dynaconf |

### AI/ML

| Library | Purpose | Alternatives |
|---------|---------|--------------|
| anthropic | Claude API for ActionGraph compilation and self-repair | openai SDK, litellm |
| sentence-transformers | 384-dim embeddings for vector search | openai embeddings, Anthropic embeddings |

### Networking/API

| Library | Purpose | Alternatives |
|---------|---------|--------------|
| httpx | Sync HTTP client for target interaction | requests, aiohttp |
| mitmproxy | Traffic capture and .mitm file parsing | Burp Suite (not embeddable), scapy |

### Database/Storage

| Library | Purpose | Alternatives |
|---------|---------|--------------|
| neo4j | Graph database driver (Cypher, vectors, HNSW) | py2neo, neomodel ORM |

### Testing

| Library | Purpose | Alternatives |
|---------|---------|--------------|
| pytest | Test runner with fixtures and markers | unittest (stdlib) |

### Development Tools

| Library | Purpose | Alternatives |
|---------|---------|--------------|
| ruff | Linting + formatting | flake8 + isort, pylint |
| black | Formatting (redundant with ruff) | ruff format |
| mypy | Type checking | pyright, pytype |

### Not Applicable

- **UI/Display**: No UI libraries (CLI-only project)
- **Security**: No dedicated security libraries (mitmproxy handles TLS; httpx handles cookies)
- **Data Processing**: Pydantic covers all parsing/validation needs

---

## 5. Dependency Health

### 5.1 Version Status

| Library | Current | Constraint | Status |
|---------|---------|-----------|--------|
| pydantic | 2.11.10 | >=2.0 | Up-to-date |
| pydantic-settings | 2.12.0 | >=2.0 | Up-to-date |
| neo4j | 6.1.0 | >=5.0 | Up-to-date |
| httpx | 0.28.1 | >=0.25.0 | Up-to-date |
| sentence-transformers | 5.2.2 | >=2.2.0 | Up-to-date |
| anthropic | 0.79.0 | >=0.20.0 | Up-to-date |
| mitmproxy | 12.2.1 | >=10.0 | Up-to-date |
| pytest | 9.0.2 | >=7.0 | Up-to-date |

### 5.2 Security Advisories

No known critical vulnerabilities in installed versions as of Feb 2026.

### 5.3 Maintenance Status

| Library | Maintainers | Status |
|---------|-------------|--------|
| pydantic | Samuel Colvin + team | Active (major releases) |
| neo4j | Neo4j Inc | Active (corporate-backed) |
| httpx | Encode (Tom Christie) | Active |
| anthropic | Anthropic | Active (corporate-backed) |
| mitmproxy | mitmproxy team | Active |
| sentence-transformers | UKPLab / Hugging Face | Active |
| pytest | pytest-dev team | Active |
| ruff | Astral (Charlie Marsh) | Active (rapid development) |

---

## Summary

### Dependency Metrics

| Metric | Value |
|--------|-------|
| Total runtime deps | 7 |
| Total dev deps | 6 |
| Outdated | 0 |
| Security issues | 0 |
| Unused (removable) | 1 (black) |

### Dependency Graph

```
llmitm_v2
├── anthropic ──────── httpx, pydantic
├── pydantic
│   └── pydantic-settings
├── neo4j
├── httpx
├── mitmproxy ──────── Flask, cryptography, ...
└── sentence-transformers ── torch, numpy, transformers, huggingface-hub
```

### Risk Assessment

| Risk | Libraries | Mitigation |
|------|-----------|------------|
| Heavy install size (~2GB) | sentence-transformers (pulls PyTorch) | Lazy import in place; could make optional dep |
| Beta API surface | anthropic (`beta.messages`, `@beta_tool`) | Pin version; monitor changelog |
| Loose version constraints | All deps use `>=` floor only | Add upper bounds or use lock file |

### Recommendations

- Remove `black` from dev deps — redundant with ruff
- Move `sentence-transformers` to optional deps — only needed for vector similarity, lazy-imported
- Add a lock file (`pip freeze` or adopt `uv`) for reproducible installs
- Pin `anthropic` more tightly (e.g. `>=0.79.0,<1.0`) — beta APIs change frequently
- Add `.venv/bin/` to `.gitignore` — untracked binaries showing in git status
