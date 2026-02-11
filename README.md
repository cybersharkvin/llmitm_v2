# LLMitM v2

**An autonomous pentesting agent for the [Claude Code Hackathon](https://cerebralvalley.ai/e/claude-code-hackathon) (Feb 10-16, 2026)**

LLMitM v2 discovers web application vulnerabilities by reasoning about where business intent and code behavior diverge. It captures live HTTP traffic via mitmdump, identifies the target's technology stack and authentication model, and builds reusable test sequences that probe for flaws like IDOR, authentication bypass, and privilege escalation.

## Core Thesis

**The LLM builds the automation that replaces itself.** Expensive LLM reasoning happens once at "compile time" to produce a deterministic ActionGraph. The system then executes that compiled artifact repeatedly without LLM involvement, converging toward zero LLM cost as the graph grows.

## How It Works

```
Phase 1 — Capture (deterministic)
  mitmdump intercepts traffic → Fingerprinter extracts target identity → hash it

Phase 2 — Lookup (deterministic)
  Query Neo4j for fingerprint hash → match found? skip to Phase 4

Phase 3 — Compile (LLM, one-time per novel fingerprint)
  Actor generates ActionGraph (CAMRO workflow) → Critic validates → store in Neo4j

Phase 4 — Execute (deterministic, zero LLM)
  Graph walker dispatches each step to its handler → threads results through chain

Phase 5 — Observe & Store (deterministic)
  Check success criteria → store Finding or classify failure → repair if systemic
```

## Hackathon Deliverable

Three demonstration runs against OWASP Juice Shop:

1. **Cold start** — Agent captures traffic, compiles an ActionGraph via actor/critic cycle, executes it, finds a vulnerability
2. **Warm start** — Second target fingerprints to a match. Stored graph executes with zero LLM calls
3. **Self-repair** — Target changes break the stored graph. LLM diagnoses, repairs the graph, stores the fix

## Core Features

- **Fingerprinting** — Identify target's tech stack, auth model, endpoint patterns, and security signals from HTTP traffic
- **ActionGraph Compilation** — LLM generates a validated, deterministic CAMRO workflow (Capture, Analyze, Mutate, Replay, Observe)
- **Actor/Critic Loop** — Actor produces ActionGraphs, Critic validates against quality criteria including over-fitting checks
- **Deterministic Execution** — Graph walker executes compiled ActionGraphs without LLM involvement
- **Self-Repair** — Three-tier failure classification (transient recoverable, transient unrecoverable, systemic) with LLM-assisted repair
- **Knowledge Accumulation** — All ActionGraphs, Fingerprints, Findings, and repair history persist in Neo4j

## Tech Stack

- **Language**: Python 3.12+
- **LLM**: Anthropic Claude via [Strands Agents SDK](https://strandsagents.com)
- **Graph Database**: Neo4j 5.x (graph-native architecture — Neo4j IS the architecture, not just storage)
- **Schema Validation**: Pydantic v2
- **Traffic Capture**: mitmproxy / mitmdump
- **Embeddings**: sentence-transformers (local, no external API)
- **Containerization**: Docker Compose

## Success Criteria

- Successfully demonstrate all three runs (cold start, warm start, self-repair) with OWASP Juice Shop
- Prove that warm start requires zero LLM calls
- Show that repaired graphs persist for future use
- Demonstrate knowledge compounding in the Neo4j graph

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
