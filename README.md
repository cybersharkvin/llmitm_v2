# LLMitM v2

**An autonomous pentesting agent for the [Claude Code Hackathon](https://cerebralvalley.ai/e/claude-code-hackathon) (Feb 10-16, 2026)**

LLMitM v2 discovers web application vulnerabilities by reasoning about where business intent and code behavior diverge. It captures live HTTP traffic via mitmdump, identifies the target's technology stack and authentication model, and builds reusable test sequences that probe for flaws like IDOR, authentication bypass, and privilege escalation.

## Core Thesis

**The LLM builds the automation that replaces itself.** Expensive LLM reasoning happens once at "compile time" to produce a deterministic ActionGraph. The system then executes that compiled artifact repeatedly without LLM involvement, converging toward zero LLM cost as the graph grows.

## E2E Results (Verified Feb 15, 2026)

Three targets verified across all four demonstration modes:

### Juice Shop (Bearer Token Auth)
| Test | Path | LLM Calls | Tokens | Findings | Status |
|------|------|-----------|--------|----------|--------|
| Cold Start | `cold_start` | 7 | ~38K | 1 IDOR | PASS |
| Warm Start | `warm_start` | 0 | 0 | 1 IDOR | PASS |
| Self-Repair | `repair` | 18 | ~134K | 1 IDOR | PASS |
| Persistence | `warm_start` | 0 | 0 | 1 IDOR | PASS |

### NodeGoat (Session Cookie Auth)
| Test | Path | LLM Calls | Tokens | Findings | Status |
|------|------|-----------|--------|----------|--------|
| Cold Start | `cold_start` | 7 | ~87K | 1 IDOR | PASS |
| Warm Start | `warm_start` | 0 | 0 | 1 IDOR | PASS |
| Self-Repair | `repair` | 9 | ~70K | 1 IDOR | PASS |
| Persistence | `warm_start` | 0 | 0 | 1 IDOR | PASS |

### DVWA (Session Cookie + CSRF Auth)
| Test | Path | LLM Calls | Tokens | Findings | Status |
|------|------|-----------|--------|----------|--------|
| Cold Start | `cold_start` | 12 | ~71K | 1 IDOR | PASS |
| Warm Start | `warm_start` | 0 | 0 | 1 IDOR | PASS |
| Self-Repair | `repair` | 8 | ~60K | 1 IDOR | PASS |
| Persistence | `warm_start` | 0 | 0 | 1 IDOR | PASS |

## How It Works

```
Phase 1 — Fingerprint (deterministic)
  Read .mitm capture → Fingerprinter extracts target identity → SHA256 hash

Phase 2 — Lookup (deterministic)
  Query Neo4j for fingerprint hash → match found? skip to Phase 4

Phase 3 — Compile (LLM, one-time per novel fingerprint)
  Recon Agent analyzes traffic via 4 tools → prescribes exploit →
  Attack Critic refines → deterministic step generation → store in Neo4j

Phase 4 — Execute (deterministic, zero LLM)
  Graph walker dispatches each CAMRO step to its handler → threads results

Phase 5 — Observe & Store (deterministic)
  Check success criteria → store Finding or classify failure → repair if systemic
```

## Architecture

```
Python Orchestrator (all control flow)
├── Anthropic API via native SDK (compile-time only)
│   ├── ProgrammaticAgent: code_execution + 4 recon tools → AttackPlan
│   └── SimpleAgent: grammar-constrained critic → refined AttackPlan
├── Neo4j via GraphRepository (ActionGraphs, Fingerprints, Findings)
├── 5 Exploit Step Generators (deterministic CAMRO step production)
├── 3 Step Handlers (HTTP, Regex, Shell — deterministic execution)
└── Pydantic v2 (contract enforcement at every boundary)
```

## Tech Stack

- **Language**: Python 3.12+
- **LLM**: Anthropic Claude Sonnet 4.5 via native SDK (structured output + programmatic tool calling)
- **Graph Database**: Neo4j 5.x (graph-native — Neo4j IS the architecture, not just storage)
- **Schema Validation**: Pydantic v2
- **Traffic Capture**: mitmproxy / mitmdump
- **HTTP Client**: httpx
- **Containerization**: Docker Compose

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Anthropic API key

## Setup

```bash
# Clone and install
git clone https://github.com/geebs/llmitm_v2.git
cd llmitm_v2
python3 -m venv .venv
.venv/bin/pip install -e .

# Copy env and fill in your Anthropic API key
cp .env.example .env

# Start all services (Neo4j, Juice Shop, NodeGoat, DVWA, mitmproxy)
make up
```

### First-Run Setup for Targets

**NodeGoat** requires a database reset on first start:
```bash
docker exec llmitm_nodegoat node artifacts/db-reset.js
```

**DVWA** requires database initialization on first start:
1. Open `http://localhost:8081/setup.php` in a browser
2. Click "Create / Reset Database"

## Running the Demo

### Juice Shop (default target)

```bash
make reset                    # Clean Neo4j slate
make run                      # Cold start — compiles ActionGraph, finds IDOR
make run                      # Warm start — zero LLM calls, reuses graph
make break-graph && make run  # Self-repair — LLM recompiles
make run                      # Persistence — repaired graph reused
```

### NodeGoat

```bash
make run-nodegoat             # Cold start
make run-nodegoat             # Warm start
make break-graph-nodegoat && make run-nodegoat  # Self-repair
make run-nodegoat             # Persistence
```

### DVWA

```bash
make run-dvwa                 # Cold start
make run-dvwa                 # Warm start
make break-graph-dvwa && make run-dvwa  # Self-repair
make run-dvwa                 # Persistence
```

Add `DEBUG_LOGGING=true` before any `make run` command to write per-API-call JSON logs to `debug_logs/<timestamp>/`.

## Exploring the Graph

Connect to Neo4j Browser at `http://localhost:7474` (user: `neo4j`, password: `password`).

```cypher
-- See the full graph
MATCH (n) RETURN n LIMIT 50

-- See the ActionGraph step chain
MATCH (ag:ActionGraph)-[:STARTS_WITH]->(s:Step)
MATCH path=(s)-[:NEXT*]->(end)
RETURN ag, path

-- See findings
MATCH (f:Finding)-[:PRODUCED_BY]->(ag) RETURN f, ag

-- See all ActionGraphs for a fingerprint (newest first)
MATCH (f:Fingerprint)-[:TRIGGERS]->(ag:ActionGraph)
RETURN f.hash, ag.id, ag.created_at ORDER BY ag.created_at DESC

-- See repair edges
MATCH ()-[r:REPAIRED_TO]->() RETURN r
```

## Running Tests

```bash
make test
```

119 tests passing, 1 skipped.

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make up` / `make down` | Start/stop Docker containers |
| `make run` | Run orchestrator (Juice Shop) |
| `make run-nodegoat` | Run orchestrator (NodeGoat) |
| `make run-dvwa` | Run orchestrator (DVWA) |
| `make test` | Run pytest suite (119 passing) |
| `make schema` | Create Neo4j constraints and indexes |
| `make reset` | Wipe graph and recreate schema |
| `make break-graph` | Corrupt Juice Shop steps for repair demo |
| `make break-graph-nodegoat` | Corrupt NodeGoat steps for repair demo |
| `make break-graph-dvwa` | Corrupt DVWA steps for repair demo |
| `make snapshot NAME=x` | Export Neo4j binary dump |
| `make restore NAME=x` | Restore from binary dump |

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
