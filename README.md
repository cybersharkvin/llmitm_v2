# LLMitM v2

Autonomous pentesting agent that compiles LLM reasoning into reusable, deterministic exploit graphs. Built for the [Claude Code Hackathon](https://cerebralvalley.ai/e/claude-code-hackathon) (Feb 10–16, 2026).

LLMitM v2 discovers web application vulnerabilities by reasoning about where business intent and code behavior diverge. It captures HTTP traffic via mitmproxy, identifies a target's technology stack and authentication model, and builds reusable test sequences that probe for flaws like IDOR, authentication bypass, and privilege escalation.

Verified end-to-end against three real vulnerable web applications — OWASP Juice Shop (bearer token), NodeGoat (session cookie), and DVWA (cookie + CSRF) — across four modes: cold start, warm start, self-repair, and persistence.

## Core Thesis

**The LLM builds the automation that replaces itself.**

Expensive LLM reasoning happens once at "compile time" to produce an ActionGraph — a validated, deterministic sequence of CAMRO steps (Capture, Analyze, Mutate, Replay, Observe) stored in Neo4j. The system executes that compiled artifact repeatedly without any LLM involvement. As the graph accumulates knowledge from each engagement, the system converges toward zero LLM cost.

First engagement is expensive. Second is free. Hundredth is still free.

This inverts the economics of every other AI-assisted security tool. Most systems use the LLM as a runtime — every action requires a model call, costs scale linearly, and knowledge dies with the session. LLMitM v2 uses the LLM as a compiler — it reasons once, compiles that reasoning into a deterministic artifact, and gets out of the way. The artifact is the product. The model is the build tool.

## What Makes This Different

### LLM-as-Compiler, Not LLM-as-Runtime

The dominant pattern in AI tooling puts the model in the hot loop: every action triggers an LLM call. LLMitM v2 treats the LLM the way a software engineer treats a compiler — it translates high-level reasoning into executable instructions, then the instructions run on their own. The "binary" is an ActionGraph. The "runtime" is a deterministic Python orchestrator that walks the graph, dispatches step handlers, and threads execution context with zero model involvement.

### Knowledge Compounds in a Graph, Not a Prompt

Most AI systems are stateless — each session starts from zero. RAG bolts retrieval onto this but doesn't solve it: retrieved context still gets fed back into the LLM for re-reasoning. LLMitM v2 stores compiled tradecraft as executable graph structure in Neo4j. When a fingerprint matches a known target, the system doesn't retrieve context and re-reason. It executes the stored ActionGraph directly. The graph IS the accumulated intelligence, not an input to more intelligence.

### Self-Repair With Persistent Memory

When a stored ActionGraph fails against a changed target, the system doesn't discard what it knows. It classifies the failure deterministically first — retries for transient errors, aborts for unrecoverable ones. Only systemic failures invoke the LLM. The model diagnoses the break, recompiles the affected portion, and stores the repaired graph with a `[:REPAIRED_TO]` edge preserving full repair history. The fix is permanent. Next execution uses the repaired graph with zero LLM calls. The system learns from its failures and never makes the same mistake twice.

### Grammar-Constrained Security Architecture

Every LLM output is grammar-constrained via Pydantic v2 structured output. The recon agent can only prescribe from exactly 5 exploit tools (`idor_walk`, `auth_strip`, `token_swap`, `namespace_probe`, `role_tamper`) enforced by `Literal[...]` type constraints at the decoding level. The model physically cannot hallucinate a tool that doesn't exist. The schema IS the security boundary — not a prompt instruction that can be ignored, but a grammar constraint that makes invalid output impossible to generate.

## Verified Results (Feb 15, 2026)

| Target | Auth Type | Cold Start | Warm Start | Self-Repair | Persistence |
|--------|-----------|------------|------------|-------------|-------------|
| Juice Shop | Bearer token | 38K tokens, 7 calls | 0 tokens, 0 calls | 134K tokens | 0 tokens, 0 calls |
| NodeGoat | Session cookie | 87K tokens, 7 calls | 0 tokens, 0 calls | 70K tokens | 0 tokens, 0 calls |
| DVWA | Cookie + CSRF | 71K tokens, 12 calls | 0 tokens, 0 calls | 60K tokens | 0 tokens, 0 calls |

119 tests passing. 0 failures. 3 targets × 4 modes = 12 verified demo paths.

## How It Works

```
Phase 1 — Fingerprint (deterministic)
  Read .mitm capture → extract target identity → SHA256 hash

Phase 2 — Lookup (deterministic)
  Query Neo4j for fingerprint hash → match found? skip to Phase 4

Phase 3 — Compile (LLM, one-time per novel fingerprint)
  Recon Agent analyzes traffic via 4 tools → prescribes exploit →
  Attack Critic refines → deterministic step generation → store in Neo4j

Phase 4 — Execute (deterministic, zero LLM)
  Graph walker dispatches each CAMRO step to handler → threads results

Phase 5 — Observe & Store (deterministic)
  Check success criteria → store Finding or classify failure → repair if systemic
```

### The Four Demonstration Modes

**Cold Start** — First encounter with a target. The Recon Agent (ProgrammaticAgent with 4 tools: `response_inspect`, `jwt_decode`, `header_audit`, `response_diff`) explores captured traffic, identifies attack opportunities with evidence, and prescribes exploit tools. The Attack Critic independently validates the plan. Deterministic step generators convert the refined plan into CAMRO steps. The ActionGraph is stored in Neo4j, executed, and findings are recorded.

**Warm Start** — Same target, second run. Fingerprint hash matches. The stored ActionGraph is retrieved and executed with zero LLM calls. The system demonstrates it learned from the first engagement and can replicate the attack instantly.

**Self-Repair** — The stored graph is deliberately corrupted (endpoint path changed via `make break-graph`). Execution hits the broken step, classifies it as SYSTEMIC, invokes the LLM to recompile, stores the repaired graph with a `[:REPAIRED_TO]` edge, and completes execution.

**Persistence** — Third run after repair. The repaired graph is reused with zero LLM calls. The fix is permanent.

## Architecture

```
Python Orchestrator (all control flow — deterministic)
├── Anthropic API via native SDK (compile-time only)
│   ├── ProgrammaticAgent: code_execution sandbox + 4 recon tools → AttackPlan
│   └── SimpleAgent: grammar-constrained critic → refined AttackPlan
├── Neo4j via GraphRepository (the persistent brain)
│   ├── (:Fingerprint) — target identity
│   ├── (:ActionGraph) — compiled tradecraft
│   ├── (:Step)-[:NEXT]->(:Step) — CAMRO execution chains
│   ├── (:Finding) — discovered vulnerabilities
│   └── [:REPAIRED_TO] — self-healing history
├── 5 Exploit Step Generators (deterministic CAMRO step production)
├── 3 Step Handlers (HTTP, Regex, Shell — deterministic execution)
└── Pydantic v2 (contract enforcement at every boundary)
```

## Real-Time Monitor

A 3D visualization frontend provides live visibility into the orchestrator's execution:

- **React 19 + ForceGraph3D + Three.js** — 3D force-directed graph renders ActionGraph nodes with status-driven visual effects (emissive glow, spike geometry, drop lines)
- **SSE streaming** from Flask/gunicorn+gevent backend — 10 typed event streams (`run_start`, `step_start`, `step_result`, `compile_iter`, `recon_result`, `critic_result`, `failure`, `repair_start`, `run_end`)
- **CompilePanel** — floating overlay shows the actor/critic reasoning in real time during cold start compilation, with expandable opportunity cards showing observation, suspected gap, and reasoning
- **Zod schema validation** at the SSE boundary ensures type safety between Python Pydantic models and TypeScript

`docker compose up` starts everything — Neo4j, targets, backend, frontend at `http://localhost:5173`.

## Quick Start

```bash
git clone https://github.com/cybersharkvin/llmitm_v2.git
cd llmitm_v2

# Set your Anthropic API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Start everything (Neo4j, targets, mitmproxy, backend, frontend)
docker compose up -d --build
```

Open `http://localhost:5173` and click Run.

### First-Run Target Setup

**NodeGoat** requires a database reset on first start:
```bash
docker exec llmitm_nodegoat node artifacts/db-reset.js
```

**DVWA** requires database initialization:
1. Open `http://localhost:8081/setup.php`
2. Click "Create / Reset Database"

## Running the Demo

Everything is controlled from the frontend UI at `http://localhost:5173`.

1. **Select a target** — Juice Shop (bearer), NodeGoat (cookie), or DVWA (cookie + CSRF)
2. **Click Reset** — wipes Neo4j for a clean slate
3. **Click Run** — cold start: compiles ActionGraph, executes, finds IDOR
4. **Click Run again** — warm start: zero LLM calls, reuses stored graph
5. **Click Break, then Run** — self-repair: LLM recompiles broken graph
6. **Click Run again** — persistence: repaired graph reused, zero LLM

The 3D graph and CompilePanel update in real time as the orchestrator executes.

## Exploring the Graph

Connect to Neo4j Browser at `http://localhost:7474` (user: `neo4j`, password: `password`).

```cypher
-- Full graph
MATCH (n) RETURN n LIMIT 50

-- ActionGraph step chain
MATCH (ag:ActionGraph)-[:STARTS_WITH]->(s:Step)
MATCH path=(s)-[:NEXT*]->(end)
RETURN ag, path

-- Findings
MATCH (f:Finding)-[:PRODUCED_BY]->(ag) RETURN f, ag

-- All ActionGraphs for a fingerprint (newest first)
MATCH (f:Fingerprint)-[:TRIGGERS]->(ag:ActionGraph)
RETURN f.hash, ag.id, ag.created_at ORDER BY ag.created_at DESC

-- Repair edges
MATCH ()-[r:REPAIRED_TO]->() RETURN r
```

## Tech Stack

- **Language**: Python 3.12+
- **LLM**: Claude Sonnet 4.5 via Anthropic native SDK (structured output + programmatic tool calling)
- **Graph Database**: Neo4j 5.x — the graph IS the architecture, not just storage
- **Schema Validation**: Pydantic v2
- **Traffic Capture**: mitmproxy / mitmdump
- **Frontend**: React 19, ForceGraph3D, Three.js, Zod
- **Backend Monitor**: Flask, gunicorn + gevent (SSE streaming)
- **HTTP Client**: httpx
- **Containerization**: Docker Compose (9 services)
- **Tests**: pytest (119 passing, no mocks)

## The Broader Thesis

LLMitM v2 is a specific implementation of a general architectural pattern: **the most powerful AI systems will be the ones that use LLMs to build persistent, executable knowledge structures — not the ones that call LLMs on every action.**

The current paradigm treats models as runtime engines. Every interaction is a fresh inference. Context windows are the only memory. Costs scale linearly. Knowledge evaporates when the session ends.

Graph-native agents invert this. The model reasons once — deeply, expensively, carefully — and compiles that reasoning into graph structure that captures what was decided, why, what evidence supports it, and how it connects to everything else the system has learned. The graph becomes the primary computational artifact. The model becomes a build tool invoked only when the graph encounters something genuinely novel.

This pattern applies anywhere you need knowledge that compounds, decisions that persist, costs that converge, failures that teach, and execution that's auditable. The LLM is the most expensive, least reliable, and hardest-to-audit component in any AI system. The less you need it at runtime, the better.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
