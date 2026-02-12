# System Patterns

## Architecture Overview

**Architecture Type**: Graph-Native Custom Logic Agent
**Database**: Neo4j (IS the architecture, not just storage)
**Orchestrator**: Python (Custom Logic owns all control flow)
**LLM Role**: Stateless compiler for discrete tasks only
**Runtime Model**: 95% deterministic graph traversal with zero LLM involvement

## Design Philosophy

| Principle | Description |
|-----------|-------------|
| **The LLM is a Compiler, Not an Interpreter** | The LLM generates automation (ActionGraphs) that replaces itself. It runs once per novel fingerprint, then the graph executes deterministically forever |
| **Minimal & Guarded LLM** | Can it be done in code? Do it in code. The LLM is only invoked when reasoning is genuinely required. When it is invoked, it is constrained by Pydantic schemas and validated by a Critic |
| **Deterministic by Default** | The orchestrator, the graph walker, the step handlers, the fingerprinters — all deterministic Python. The LLM is the exception, not the rule |
| **Knowledge Compounds in the Graph** | Every compilation, every repair, every finding enriches the graph. The asset is the graph, not the model |
| **Strict Separation of Concerns** | The LLM never touches the network, the filesystem, or the graph directly. Tools mediate all access |
| **Test Reality, Not Implementation** | Tests must not use mocks; they test from user perspective. Real code, real inputs, real outputs |

## Testing Philosophy

**Mandatory rules for all tests in this project:**

1. **Max 5 lines per test body** — Keep tests focused and concise. Use fixtures to reduce setup boilerplate.
2. **No mocks or fakes** — Use real code with real inputs and assertions on real outputs.
3. **User perspective only** — Test as if calling the library from the outside; never test internal implementation details.
4. **Graceful external dependency handling** — Tests requiring Neo4j, HTTP, or filesystem must skip gracefully if unavailable via `pytest.skip()`.
5. **Mark integration tests** — Use `@pytest.mark.integration` for tests that require external services.

**What this means:**
- ✅ Call real Pydantic models with real data
- ✅ Use real Neo4j connections (skip if unavailable)
- ✅ Test JSON serialization with real `json` module
- ✅ Mark external service tests with `@pytest.mark.integration`
- ❌ Never use `unittest.mock`, `MagicMock`, `patch`, or `monkeypatch`
- ❌ Never test internal implementation details
- ❌ Never skip tests without a documented reason (e.g., "Neo4j unavailable")

## Design Patterns

### Repository Pattern
- **Description**: `GraphRepository` class encapsulates all Cypher queries behind semantic methods
- **When to Use**: All Neo4j access goes through GraphRepository
- **Example**: `graph_repo.get_action_graph_by_fingerprint(fingerprint_hash)`
- **Rationale**: Single class, mockable, testable, hides Cypher complexity

### Strategy Pattern
- **Description**: Different context assembly functions for different phases
- **When to Use**: Before each LLM call to build minimal, relevant context
- **Example**: `assemble_compilation_context()`, `assemble_repair_context()`
- **Rationale**: Context hygiene — each phase needs different information

### Actor/Critic Pattern
- **Description**: Two single-shot LLM calls in while loop: Actor produces, Critic validates
- **When to Use**: ActionGraph compilation and major repairs (at *compile time*, not runtime)
- **Example**: Actor generates graph → Critic validates → loop until `critic_result.passed` or max iterations
- **Rationale**: Quality control on LLM outputs, catches over-fitting and logic errors. Used for compilation, not execution

### Abstract Base Class + Concrete Implementation
- **Description**: `StepHandler` ABC and `Fingerprinter` ABC with concrete implementations per type
- **When to Use**: Adding new execution capabilities or fingerprinting dimensions
- **Example**: `class MitmdumpStepHandler(StepHandler): def execute(...)`. ABCs inherit directly from `ABC` (not `abc.ABCMeta`) to ensure ctags detection
- **Rationale**: Plugin architecture. New capabilities added by writing one class and registering it. Zero changes to core

### Factory Pattern
- **Description**: `create_*` functions construct configured objects with injected dependencies
- **When to Use**: Creating complex objects (Agent, GraphRepository, Orchestrator)
- **Example**: `create_actor_agent()`, `create_critic_agent()`, `create_graph_repository()`
- **Rationale**: Named with `create_` prefix for ctags architectural visibility, centralizes configuration

### Singleton Pattern
- **Description**: Neo4j `Driver` instance created once, injected everywhere
- **When to Use**: Database connections
- **Example**: `driver = GraphDatabase.driver(uri, auth)` → passed to all Repository instances
- **Rationale**: Official Neo4j best practice. Manages connection pool efficiently

### Recon Agent / Critic Pattern
- **Description**: LLM-driven recon agent with tools explores target through mitmproxy, critic validates the structured ReconReport
- **When to Use**: Live target exploration (capture_mode=live) replacing static traffic files
- **Example**: `recon_agent(prompt, structured_output_model=ReconReport)` → critic validates → `ReconReport.to_fingerprint()` → existing warm-start flow
- **Key Files**: `capture/launcher.py` (lifecycle), `tools/recon_tools.py` (http_request/shell_command), `models/recon.py` (ReconReport), `orchestrator/agents.py` (create_recon_agent)
- **Rationale**: LLM-driven exploration discovers more endpoints and identifies vulns that rule-based fingerprinting misses. tool_context audit trail lets critic verify claims.

### Quick Fingerprint Fast Path
- **Description**: Send 3 deterministic HTTP requests, extract fingerprint from headers — zero LLM cost for known targets
- **When to Use**: First step in live mode before invoking expensive recon agent
- **Example**: `quick_fingerprint(target_url, proxy_port)` → Fingerprint → check Neo4j → if match, skip recon entirely
- **Rationale**: Preserves "convergence toward zero LLM cost" thesis. Second run against same target = zero tokens.

### Dependency Injection
- **Description**: Dependencies passed explicitly to constructors throughout the stack
- **When to Use**: Every component construction
- **Example**: Driver → Repository → Context Assemblers → Orchestrator
- **Rationale**: Loose coupling, testable, mockable

### Data Transfer Object (DTO)
- **Description**: Pydantic models for all data transfer between layers
- **When to Use**: LLM outputs, graph storage, application boundaries
- **Example**: `Fingerprint`, `ActionGraph`, `CriticFeedback`, `RepairDiagnosis`
- **Rationale**: Typed contracts, validation, type safety throughout

### Handler Registry Pattern
- **Description**: `HANDLER_REGISTRY` maps `StepType` → `Type[StepHandler]`, `get_handler()` instantiates
- **When to Use**: Dispatching step execution by type during ActionGraph traversal
- **Example**: `handler = get_handler(step.type); result = handler.execute(step, context)`
- **Rationale**: New step types added by writing one handler class and one registry entry. Zero changes to orchestrator

### Rule-Based Fingerprinting
- **Description**: `Fingerprinter` extracts target identity from HTTP response headers and traffic patterns (deterministic, no ML)
- **When to Use**: Identifying targets for warm/cold start routing
- **Example**: `fp = Fingerprinter().fingerprint(traffic_log)` → `tech_stack`, `auth_model`, `endpoint_pattern`, `security_signals`
- **Signals Extracted**: X-Powered-By header, Authorization header format, API endpoint prefixes, CORS/CSP headers
- **Rationale**: Deterministic-first philosophy; no ML model required; works offline; 100% reproducible output

### Deterministic-First with LLM Fallback
- **Description**: Simple classification logic handles obvious cases, LLM only for ambiguous
- **When to Use**: Self-repair failure classification
- **Example**: `if error_code == 404: return "transient_unrecoverable"` else ask LLM
- **Rationale**: Minimize LLM costs, handle 80% of failures deterministically

## Component Structure

```
Python Orchestrator (Custom Logic — programmatic flow control)
├── Anthropic API via Strands (reasoning — compilation and repair only)
├── Neo4j via GraphRepository (knowledge — action graphs, fingerprints, findings)
├── mitmdump via subprocess (execution — deterministic CAMRO operations)
└── Pydantic (contract enforcement — every boundary)
```

## Data Flow

### Compilation Flow (Cold Start)
1. Capture traffic from target → Extract Fingerprint
2. Query Neo4j for exact match on Fingerprint hash
3. If no match: Vector search for similar Fingerprints
4. If novel: Assemble compilation context (fingerprint + traffic + similar graphs)
5. Actor/Critic loop generates validated ActionGraph
6. Store ActionGraph in Neo4j linked to Fingerprint

### Execution Flow (Warm Start)
1. Fetch ActionGraph and ordered Steps via GraphRepository
2. For each Step in chain:
   - Look up handler from registry by `step.type`
   - Construct ExecutionContext from accumulated state
   - Call `handler.execute(step, context)` → StepResult
   - If `success_criteria` matches: record Finding
   - If error: `classify_failure()` → repair tier → retry/restart/repair
   - Thread StepResult into next step's context

### Self-Repair Flow
1. Step execution fails → Capture error log and HTTP status code
2. Deterministic classification first (timeouts, 404, 503, session expired)
3. LLM fallback for ambiguous errors → RepairDiagnosis
4. Three tiers:
   - **Transient recoverable**: Retry step immediately
   - **Transient unrecoverable**: Restart full ActionGraph
   - **Systemic**: LLM repairs graph, creates `[:REPAIRED_TO]` edge, stores fix

## Neo4j Graph Schema

**See `neo4jSchema.md` for complete Neo4j architecture, schema details, query patterns, and integration examples.**

### Quick Reference

**Core Nodes:** `(:Fingerprint)`, `(:ActionGraph)`, `(:Step)`, `(:Finding)`

**Core Relationships:**
- `(:Fingerprint)-[:TRIGGERS]->(:ActionGraph)` — routing relationship
- `(:ActionGraph)-[:STARTS_WITH]->(:Step)` — step chain entry point
- `(:Step)-[:NEXT]->(:Step)` — CAMRO execution order
- `(:Step)-[:REPAIRED_TO]->(:Step)` — self-healing history
- `(:Finding)-[:PRODUCED_BY]->(:ActionGraph)` — finding attribution
- `(:Fingerprint)-[:SIMILAR_TO]->(:Fingerprint)` — fuzzy similarity cache

## Naming Conventions

### Files
- **Python modules**: `snake_case.py` (e.g., `graph_repository.py`, `step_handler.py`)

### Code
- **Classes**: `PascalCase` (e.g., `GraphRepository`, `ActionGraph`)
- **ABCs**: `PascalCase`, inherits `ABC` directly (e.g., `class StepHandler(ABC)`)
- **Factory Functions**: `create_<thing>` (e.g., `create_actor_agent()`, `create_graph_repository()`)
- **Functions**: `snake_case` verb phrase (e.g., `assemble_compilation_context()`, `classify_failure()`)
- **Methods**: `snake_case` verb phrase (e.g., `get_action_graph_by_fingerprint()`, `find_similar_action_graphs()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_CRITIC_ITERATIONS`, `DEFAULT_SIMILARITY_THRESHOLD`)
- **Pydantic Models**: `PascalCase` noun (e.g., `Fingerprint`, `CriticFeedback`, `RepairDiagnosis`)

### Neo4j Conventions
- **Node Labels**: `PascalCase` noun (e.g., `(:Fingerprint)`, `(:ActionGraph)`, `(:Step)`)
- **Relationships**: `UPPER_SNAKE_CASE` verb phrase (e.g., `[:HAS_STEP]`, `[:REPAIRED_TO]`, `[:TESTS_FOR]`)
- **Properties**: `snake_case` (e.g., `tech_stack`, `observation_embedding`, `success_criteria`)

### Tool Functions
- **Strands @tool functions**: `snake_case` verb phrase (e.g., `find_similar_action_graphs`, `get_repair_history`)

## ctags Compatibility

The naming conventions are designed to produce clean output from the `ctags-arch.sh` script:

| Script Section | What It Detects | Our Convention That Matches |
|----------------|-----------------|----------------------------|
| **Abstract Base Classes** | `inherits == "ABC"` | ABCs inherit directly from `ABC`, never `abc.ABCMeta` |
| **Concrete Implementations** | `inherits != false and inherits != "ABC"` | Concrete classes inherit from the ABC by name (e.g., `StepHandler`) |
| **Factory Functions** | Name contains `create`, `factory`, `build`, or `make` | All factory functions use the `create_` prefix |
| **All Classes** | `kind == "class"` | `PascalCase` class names |
| **All Functions** | `kind == "function"` | `snake_case` function names |
| **All Methods** | `kind == "member"` | `snake_case` method names |

## Error Handling Patterns

### Deterministic Classification First
```python
def classify_failure(error_log: str, status_code: int) -> str:
    if status_code == 404:
        return "transient_unrecoverable"  # Endpoint gone
    if status_code == 503:
        return "transient_recoverable"  # Service overloaded
    if "timeout" in error_log.lower():
        return "transient_recoverable"  # Network issue
    if "session expired" in error_log.lower():
        return "transient_unrecoverable"  # Need fresh session
    # Only ambiguous cases hit LLM
    return ask_llm_for_diagnosis(error_log, status_code)
```

### LLM-Guarded Execution
All LLM outputs validated via Pydantic:
```python
agent = create_actor_agent()
response = agent.run(
    prompt=compilation_context,
    structured_output_model=ActionGraph  # Pydantic enforces schema
)
# response is guaranteed to match ActionGraph schema or raises ValidationError
```

## State Management

**Neo4j is the only stateful component.** There is no in-memory state, no session files, no Redis. The graph stores:

- **`(:Fingerprint)`** — target identity and characteristics
- **`(:ActionGraph)`** — compiled workflow logic (the reusable asset)
- **`(:Step)`** — individual execution steps within an ActionGraph
- **`(:Finding)`** — discovered vulnerabilities and observations
- **`[:REPAIRED_TO]`** — repair history linking old steps to new ones
- **`[:SIMILAR_TO]`** — fuzzy similarity edges between fingerprints

**The Python process is stateless.** If it crashes, the graph retains everything. The orchestrator resumes by querying the graph for the current state.

### Execution State (Ephemeral)
- **session_tokens**: Dict stored in ExecutionContext, keys are literal HTTP header names (e.g., `"Authorization"`) → merged directly into request headers
- **cookies**: Dict stored in ExecutionContext, keys are cookie names → set via `httpx.Client(cookies=...)`, updated from `Set-Cookie` responses
- **previous_outputs**: List accumulated during graph traversal, discarded after run completes
- **current_step_index**: Tracked by orchestrator loop during execution only

### State Transitions
- **Cold → Warm**: First successful execution creates reusable graph in Neo4j
- **Warm → Repair**: Execution failure triggers repair diagnosis
- **Repair → Warm**: Repaired graph stored in Neo4j, returns to normal execution

---

**Update Frequency**: After establishing new patterns or making architectural decisions
