# Project Brief

## Project Goal

LLMitM v2 is an autonomous pentesting agent that discovers web application vulnerabilities by reasoning about where business intent and code behavior diverge. It captures live HTTP traffic via mitmdump, identifies the target's technology stack and authentication model, and builds reusable test sequences that probe for flaws like IDOR, authentication bypass, and privilege escalation.

**Core Thesis:** The LLM builds the automation that replaces itself. The expensive LLM reasoning happens once at "compile time" to produce a deterministic ActionGraph. The system then executes that compiled artifact repeatedly without LLM involvement, converging toward zero LLM cost as the graph grows.

**Target Audience:** Security researchers and penetration testers who need automated, repeatable vulnerability testing that learns from past engagements and compounds knowledge over time.

## Core Requirements

### Hackathon Deliverable (Feb 10-16, 2026)

**Three demonstration runs:**
1. **Cold start**: Agent captures traffic from OWASP Juice Shop, compiles an ActionGraph via actor/critic cycle, executes it, finds a vulnerability
2. **Warm start**: Second target fingerprints to a match. Stored graph executes with zero LLM calls
3. **Self-repair**: Target changes break the stored graph. LLM diagnoses, repairs the graph, stores the fix

### Core Features

- **Fingerprinting**: Identify target's tech stack, auth model, endpoint patterns, and security signals from HTTP traffic
- **ActionGraph Compilation**: LLM generates a validated, deterministic workflow (CAMRO: Capture, Analyze, Mutate, Replay, Observe) for testing specific vulnerability types
- **Actor/Critic Loop**: Actor produces ActionGraphs, Critic validates them against quality criteria including over-fitting checks
- **Deterministic Execution**: Graph walker executes compiled ActionGraphs without LLM involvement
- **Self-Repair**: Three-tier failure classification (transient recoverable, transient unrecoverable, systemic) with LLM-assisted repair for systemic failures
- **Knowledge Accumulation**: All ActionGraphs, Fingerprints, Findings, and repair history persist in Neo4j

## Success Criteria

- Successfully demonstrate all three runs (cold start, warm start, self-repair) with OWASP Juice Shop
- Prove that warm start requires zero LLM calls
- Show that repaired graphs persist for future use
- Demonstrate knowledge compounding in the Neo4j graph

## Out of Scope

### Post-Hackathon Features
- Multi-target parallel execution
- Path compilation / node promotion optimization
- Five-tier query routing (hackathon uses exact match + full compilation only)
- Event bus architecture (hackathon uses sequential flow)
- Frontend visualization
- Organizational reasoning as stored graph nodes
- Multiple concurrent agents

## User Stories

**Security Researcher**: "I test multiple similar web applications. When I encounter a new target, I want the system to recognize familiar patterns and reuse proven exploitation techniques without requiring me to manually configure tests or wait for LLM processing."

**Penetration Tester**: "When my automated tests break due to target changes, I need the system to intelligently diagnose whether it's a temporary glitch or requires a fundamental strategy change, and automatically repair the workflow when possible."

**Red Team Operator**: "I want to accumulate knowledge across engagements so that each new target builds on lessons learned from previous ones, creating a compounding intelligence asset that gets better over time."

---

**Update Frequency**: Rarely (only when scope genuinely changes)
