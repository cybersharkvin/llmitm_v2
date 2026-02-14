# LLMitM v2

**An autonomous pentesting agent for the [Claude Code Hackathon](https://cerebralvalley.ai/e/claude-code-hackathon) (Feb 10-16, 2026)**

LLMitM v2 discovers web application vulnerabilities by reasoning about where business intent and code behavior diverge. It captures live HTTP traffic via mitmdump, identifies the target's technology stack and authentication model, and builds reusable test sequences that probe for flaws like IDOR, authentication bypass, and privilege escalation.

## Core Thesis

**The LLM builds the automation that replaces itself.** Expensive LLM reasoning happens once at "compile time" to produce a deterministic ActionGraph. The system then executes that compiled artifact repeatedly without LLM involvement, converging toward zero LLM cost as the graph grows.

## E2E Results (Verified Feb 13, 2026)

All 4 demonstration runs pass against OWASP Juice Shop:

| Test | Path | LLM Calls | Tokens | Findings | Status |
|------|------|-----------|--------|----------|--------|
| 1. Cold Start | `cold_start` | 7 | ~37K | 1 IDOR | PASS |
| 2. Warm Start | `warm_start` | 0 | 0 | 1 IDOR | PASS |
| 3. Self-Repair | `repair` | 9 | ~56K | 1 IDOR | PASS |
| 4. Persistence | `warm_start` | 0 | 0 | 1 IDOR | PASS |

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

# Start Neo4j + Juice Shop
make up
```

## Running the Demo

```bash
# Reset graph (clean slate)
make reset

# Test 1 — Cold start (compiles ActionGraph, finds IDOR vulnerability)
DEBUG_LOGGING=true make run

# Test 2 — Warm start (zero LLM calls, reuses stored graph)
DEBUG_LOGGING=true make run

# Test 3 — Self-repair (corrupt graph, LLM recompiles)
make break-graph
DEBUG_LOGGING=true make run

# Test 4 — Persistence (repaired graph reused, zero LLM calls)
DEBUG_LOGGING=true make run
```

Debug logs are written to `debug_logs/<timestamp>/` including per-API-call JSON and `run_summary.json`.

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
```

## Running Tests

```bash
make test
```

96 tests passing, 1 skipped.

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make up` / `make down` | Start/stop Docker containers |
| `make run` | Run the orchestrator |
| `make test` | Run pytest suite |
| `make schema` | Create Neo4j constraints and indexes |
| `make reset` | Wipe graph and recreate schema |
| `make break-graph` | Corrupt steps for self-repair demo (GET→PATCH) |
| `make fix-graph` | Reverse corruption (manual fallback) |
| `make snapshot NAME=x` | Export Neo4j binary dump |
| `make restore NAME=x` | Restore from binary dump |

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
