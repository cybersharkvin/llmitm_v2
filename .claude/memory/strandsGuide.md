# Strands SDK Integration Guide

## Overview

**Strands SDK is used as a library, not a framework.** The LLMitM v2 orchestrator calls the Strands `Agent` class for discrete reasoning tasks (compilation, repair), then discards it. The Agent does not control the application flow — the Custom Logic Orchestrator does.

**Philosophy:** "The LLM is a Compiler, Not an Interpreter" — Strands Agent generates automation (ActionGraphs) once, then deterministic execution takes over forever.

---

## What We Use from Strands

| Feature | Purpose | Location |
|---------|---------|----------|
| **`Agent` class** | Single-shot LLM compiler | `llmitm/orchestrator/compiler.py` |
| **`@tool` decorator** | Graph query tools for LLM | `llmitm/tools/graph_tools.py` |
| **`structured_output_model`** | Pydantic validation on every LLM call | All orchestrator phases |
| **`SequentialToolExecutor`** | Preserve tool call dependency chains | Agent configuration |
| **`NullConversationManager`** | Disable conversational history | Agent configuration |
| **`BeforeToolCallEvent` hook** | Human-in-the-loop approval | `llmitm/hooks/approval_hook.py` |
| **`ToolContext`** | Access agent state, interrupt capability | Tool implementations |

---

## What We Don't Use (and Why)

| Feature | Why NOT Used |
|---------|--------------|
| **`SessionManager` / `FileSessionManager`** | Neo4j is the single source of truth for all state |
| **`AgentState`** | State lives in the graph, not in the SDK |
| **`SlidingWindowConversationManager`** | Context managed explicitly via assembly functions |
| **Multi-Agent (`Swarm`, `Graph`)** | Single Custom Logic Orchestrator architecture |
| **`ConcurrentToolExecutor`** | Would break tool call dependency chains |
| **Persistent Agent Loop** | Agent called once per task, then discarded |

---

## Core Integration Patterns

### 1. Agent as Single-Shot Compiler

**NOT a persistent conversational agent:**

```python
from strands import Agent
from strands.agent.conversation_manager import NullConversationManager
from strands.tools.executors import SequentialToolExecutor

def create_actor_agent(graph_repo: GraphRepository) -> Agent:
    """Create Actor agent for ActionGraph compilation."""

    tools = [
        create_find_similar_tool(graph_repo),
        create_get_repair_history_tool(graph_repo)
    ]

    system_prompt = """
    You are a security testing automation compiler. Generate ActionGraphs
    (test workflows) for security testing based on target fingerprints.

    Guidelines:
    - Use CAMRO phases: Capture, Analyze, Mutate, Replay, Observe
    - Each step must be deterministic and executable via CLI tools
    - Include success_criteria regex patterns for validation
    """

    return Agent(
        model="us.anthropic.claude-sonnet-4-20250514-v1:0",
        system_prompt=system_prompt,
        tools=tools,
        conversation_manager=NullConversationManager(),  # No memory
        tool_executor=SequentialToolExecutor()  # Preserve dependencies
    )

# Usage: Orchestrator calls agent once, then discards it
def compile_action_graph(fingerprint: Fingerprint) -> ActionGraph:
    context = assemble_compilation_context(fingerprint, graph_repo)
    agent = create_actor_agent(graph_repo)  # Fresh instance

    result = agent(
        prompt=context,
        structured_output_model=ActionGraph  # Pydantic enforces schema
    )

    # Agent is discarded here, orchestrator continues
    return result.structured_output
```

---

### 2. Structured Output: LLM → Pydantic → Neo4j Bridge

**Most critical Strands feature for LLMitM v2:**

```python
from pydantic import BaseModel, Field
from typing import List

# Pydantic schema serves triple duty:
# 1. LLM output validation
# 2. Type safety in Python
# 3. Neo4j serialization contract

class Step(BaseModel):
    order: int = Field(description="Execution order")
    phase: str = Field(description="CAMRO phase")
    command: str = Field(description="Exact command to execute")
    success_criteria: Optional[str] = Field(description="Regex for validation")

class ActionGraph(BaseModel):
    vulnerability_type: str = Field(description="Type tested")
    description: str = Field(description="Human-readable explanation")
    steps: List[Step] = Field(description="Ordered CAMRO steps")

# Agent call with structured output constraint
result = actor_agent(
    prompt=compilation_context,
    structured_output_model=ActionGraph  # Pydantic enforces structure
)

# Guaranteed to match schema or ValidationError raised
action_graph: ActionGraph = result.structured_output

# Persist to Neo4j via GraphRepository
graph_repo.save_action_graph(fingerprint, action_graph)
```

**Data Flow:**
```
Context Assembly (Neo4j) → Agent Call → Pydantic Validation → Neo4j Storage
```

---

### 3. Tools: Graph Query Functions

**Pattern: Tool → Repository → Cypher → Graph**

```python
from strands import tool

@tool
def find_similar_action_graphs(description: str, top_k: int = 5) -> str:
    """Find ActionGraphs for targets similar to the one described.

    Args:
        description: Natural language description of target characteristics
        top_k: Number of similar results to return
    """
    # 1. Generate embedding
    embedding = embedding_model.encode(description)

    # 2. Query Neo4j via GraphRepository (NOT direct Cypher)
    similar = graph_repo.find_similar_fingerprints(embedding, top_k)

    # 3. Format for LLM consumption (text, not JSON)
    return format_similar_results(similar)

@tool
def get_repair_history(fingerprint_hash: str, max_results: int = 10) -> str:
    """Retrieve historical repair attempts for a fingerprint.

    Args:
        fingerprint_hash: Unique hash identifying the target
        max_results: Maximum number of repair records to return
    """
    repairs = graph_repo.get_repairs_by_fingerprint(fingerprint_hash, max_results)

    if not repairs:
        return "No repair history found for this fingerprint"

    formatted = []
    for repair in repairs:
        formatted.append(f"""
        Failed Step: {repair['failed_step']['command']}
        Error Type: {repair['failure_type']}
        Repair: {repair['repair_step']['command']}
        Success: {'Yes' if repair['success'] else 'No'}
        """)

    return "\n".join(formatted)
```

**Tool Best Practices:**
1. **Descriptive docstrings** — LLM uses these to decide when to call the tool
2. **Type hints required** — Strands generates tool schema from annotations
3. **Call GraphRepository** — Don't execute Cypher directly in tools
4. **LLM-friendly output** — Return readable text, not JSON or raw data
5. **Handle empty results** — Return helpful messages, not empty strings

---

### 4. Context Assembly: Explicit, Phase-Specific

**Philosophy: Context Hygiene — LLM receives only phase-relevant information**

```python
def assemble_compilation_context(
    fingerprint: Fingerprint,
    traffic_log: str,
    graph_repo: GraphRepository
) -> str:
    """Assemble minimal context for ActionGraph compilation."""

    # 1. Generate embedding for semantic search
    description = f"{fingerprint.tech_stack} {fingerprint.auth_model}"
    embedding = embedding_model.encode(description)

    # 2. Query for similar ActionGraphs (top 3 only)
    similar = graph_repo.find_similar_fingerprints(embedding, top_k=3)

    # 3. Format as structured prompt
    context = f"""
    # Target Fingerprint
    Tech Stack: {fingerprint.tech_stack}
    Auth Model: {fingerprint.auth_model}
    Endpoint Pattern: {fingerprint.endpoint_pattern}
    Security Signals: {', '.join(fingerprint.security_signals)}

    # Traffic Log (Sample)
    {traffic_log[:1000]}...

    # Similar ActionGraphs (for reference)
    """

    for idx, result in enumerate(similar, 1):
        ag = result['action_graph']
        context += f"""
        ## Similar Target {idx} (similarity: {result['score']:.2f})
        Name: {ag['name']}
        Vulnerability: {ag['vulnerability_type']}
        Success Rate: {ag['times_succeeded'] / ag['times_executed']:.1%}
        Steps: {len(result['steps'])} steps
        """

    return context

def assemble_repair_context(
    failed_step: Step,
    error_log: str,
    execution_history: List[str],
    graph_repo: GraphRepository
) -> str:
    """Assemble context for self-repair phase."""

    # Query for similar past repairs
    past_repairs = graph_repo.find_similar_repairs(error_log, top_k=5)

    context = f"""
    # Failed Step
    Command: {failed_step.command}
    Phase: {failed_step.phase}
    Expected Output: {failed_step.success_criteria}

    # Error Log
    {error_log}

    # Execution History (Previous Steps)
    """

    for idx, step_result in enumerate(execution_history, 1):
        context += f"{idx}. {step_result}\n"

    context += "\n# Similar Past Repairs\n"
    for repair in past_repairs:
        context += f"""
        - Original Command: {repair['failed_command']}
          Error Type: {repair['error_type']}
          Repair Command: {repair['repair_command']}
          Outcome: {'Success' if repair['success'] else 'Failed'}
        """

    return context
```

**Why Explicit Context Assembly:**
- No hidden state from previous LLM calls
- Each call is self-contained and debuggable
- Clear separation between compilation and repair contexts
- Prevents context pollution

---

### 5. Actor/Critic Pattern (Explicit Loop)

**Orchestrator controls iteration, not Strands:**

```python
def compile_action_graph_with_critic(
    fingerprint: Fingerprint,
    traffic_log: str
) -> ActionGraph:
    """Compile ActionGraph with Actor/Critic validation loop."""

    # Create agents
    actor = create_actor_agent(graph_repo)
    critic = create_critic_agent()

    # Assemble initial context
    context = assemble_compilation_context(fingerprint, traffic_log, graph_repo)

    # Explicit Actor/Critic loop (orchestrator controls)
    max_iterations = 5
    for iteration in range(max_iterations):
        # Actor generates ActionGraph
        actor_result = actor(
            prompt=context,
            structured_output_model=ActionGraph
        )
        action_graph = actor_result.structured_output

        # Critic validates ActionGraph
        critic_prompt = f"""
        Evaluate this ActionGraph for quality and generalization:

        {action_graph.model_dump_json(indent=2)}

        Validation criteria:
        - All steps deterministic (no manual intervention)
        - Commands executable via standard tools
        - Success criteria are specific regex patterns
        - No overfitting to single target
        - Proper CAMRO phase ordering
        """

        critic_result = critic(
            prompt=critic_prompt,
            structured_output_model=CriticFeedback
        )
        feedback = critic_result.structured_output

        # Check if passed
        if feedback.passed:
            # Success: persist to Neo4j
            graph_repo.save_action_graph(fingerprint, action_graph)
            return action_graph

        # Add feedback to context for next iteration
        context += f"\n\n## Critic Feedback (Iteration {iteration + 1})\n{feedback.feedback}"

    # Max iterations reached
    raise CompilationFailedException(
        f"Failed to pass Critic validation after {max_iterations} iterations"
    )
```

**Why Explicit Loop:**
- Transparent control flow (can set breakpoints)
- Easy to add logging, metrics, debugging
- Can customize retry logic (exponential backoff, etc.)
- Avoids hidden framework magic

---

### 6. Hooks: Human-in-the-Loop Approval

**Pattern: BeforeToolCallEvent → interrupt() → User Input**

```python
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent

class ApprovalHook(HookProvider):
    """Pause execution before destructive actions for human approval."""

    def __init__(self, app_name: str, destructive_patterns: list[str]):
        self.app_name = app_name
        self.destructive_patterns = destructive_patterns

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self.check_approval)

    def check_approval(self, event: BeforeToolCallEvent) -> None:
        # Extract command from tool call
        tool_name = event.tool_use["name"]
        params = event.tool_use["input"]
        command = params.get("command", "")

        # Check if destructive
        if any(pattern in command for pattern in self.destructive_patterns):
            # Pause and request approval
            approval = event.interrupt(
                f"{self.app_name}-approval",
                reason={
                    "tool": tool_name,
                    "command": command,
                    "target": params.get("target_url")
                }
            )

            # Check response
            if approval.lower() not in ["y", "yes"]:
                # Cancel tool execution
                event.cancel_tool = (
                    f"User denied approval for command: {command}"
                )

# Register with agent
approval_hook = ApprovalHook(
    app_name="llmitm",
    destructive_patterns=["DELETE", "DROP", "MUTATE", "EXPLOIT"]
)

agent = Agent(
    tools=[execute_mutation],
    hooks=[approval_hook]
)
```

**What Happens:**
1. Tool about to execute
2. Hook detects destructive pattern
3. `event.interrupt()` pauses execution
4. User prompted (CLI or UI)
5. User input returned to hook
6. Hook cancels or allows execution

---

## Configuration Choices Explained

### NullConversationManager

**What it does:** Disables automatic conversation history management.

**Why we use it:**
- Each LLM call should be self-contained (no leaked state)
- Context is explicitly assembled for each task
- Prevents context pollution between compilation/repair phases

**Code:**
```python
from strands.agent.conversation_manager import NullConversationManager

agent = Agent(
    conversation_manager=NullConversationManager()  # No memory between calls
)
```

---

### SequentialToolExecutor

**What it does:** Forces tools to execute one at a time, in order.

**Why we use it:**
During compilation, LLM might call:
1. `find_similar_action_graphs("SQL injection")`
2. `get_repair_history(graph_id)` ← depends on result from #1

Concurrent execution would break this dependency.

**Code:**
```python
from strands.tools.executors import SequentialToolExecutor

agent = Agent(
    tool_executor=SequentialToolExecutor()  # Preserve dependencies
)
```

**Alternative (NOT used):** `ConcurrentToolExecutor` (Strands default)
- Runs tools in parallel for speed
- Would break dependency chains

---

## Writing New Tools

**Template:**

```python
from strands import tool
from typing import Optional

@tool
def your_graph_query_tool(
    parameter1: str,
    parameter2: int = 10,
    optional_filter: Optional[str] = None
) -> str:
    """Brief description for LLM to understand when to use this tool.

    Args:
        parameter1: Description of first parameter
        parameter2: Description with default value
        optional_filter: Description of optional parameter
    """
    # 1. Call GraphRepository method
    results = graph_repo.query_method(parameter1, parameter2, optional_filter)

    # 2. Format for LLM consumption
    if not results:
        return "No results found"

    formatted = []
    for idx, result in enumerate(results, 1):
        formatted.append(f"{idx}. {result['name']} - {result['description']}")

    # 3. Return text (LLM receives this)
    return "\n".join(formatted)
```

**Checklist:**
- [ ] Descriptive docstring (LLM uses this)
- [ ] Type hints on all parameters
- [ ] Calls `GraphRepository`, not direct Cypher
- [ ] Returns readable text, not JSON
- [ ] Handles empty results gracefully

---

## Writing New Hooks

**Template:**

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent, AfterToolCallEvent

class YourHook(HookProvider):
    """Brief description of what this hook does."""

    def __init__(self, config_param: str):
        self.config_param = config_param

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        """Register callbacks for specific events."""
        registry.add_callback(BeforeToolCallEvent, self.before_tool)
        registry.add_callback(AfterToolCallEvent, self.after_tool)

    def before_tool(self, event: BeforeToolCallEvent) -> None:
        """Called before every tool execution."""
        tool_name = event.tool_use["name"]
        # Can inspect: event.tool_use, event.agent
        # Can cancel: event.cancel_tool = "reason"
        # Can interrupt: approval = event.interrupt("id", reason={...})

    def after_tool(self, event: AfterToolCallEvent) -> None:
        """Called after every tool execution."""
        # Can inspect: event.tool_use, event.result
        # Can modify: event.result = modified_result

# Register with agent
your_hook = YourHook(config_param="value")
agent = Agent(hooks=[your_hook])
```

**Available Events:**
- `BeforeInvocationEvent` — Agent invocation starts
- `AfterInvocationEvent` — Agent invocation completes
- `BeforeToolCallEvent` — Before tool execution (can cancel/modify)
- `AfterToolCallEvent` — After tool execution (can modify result)
- `BeforeModelCallEvent` — Before LLM inference
- `AfterModelCallEvent` — After LLM inference (can retry)

---

## Architecture Comparison

### Framework Pattern (NOT how we work)

```python
# Strands as framework (controls main loop)
agent = Agent(conversation_manager=SlidingWindow())
while True:
    user_input = input("User: ")
    response = agent(user_input)  # Agent maintains state
    print(response)
```

### Library Pattern (LLMitM v2)

```python
# Strands as library (orchestrator controls flow)
class Orchestrator:
    def compile_action_graph(self, fingerprint: Fingerprint) -> ActionGraph:
        # 1. Query graph
        similar = graph_repo.find_similar_fingerprints(fingerprint)

        # 2. Assemble context
        context = assemble_compilation_context(fingerprint, similar)

        # 3. Call agent (single-shot utility)
        agent = create_actor_agent()
        result = agent(context, structured_output_model=ActionGraph)

        # 4. Persist to graph
        graph_repo.save_action_graph(result.structured_output)

        # 5. Agent discarded, orchestrator continues
        return result.structured_output
```

**Key Differences:**

| Aspect | Framework | Library (LLMitM v2) |
|--------|-----------|---------------------|
| **Control Flow** | Framework controls loop | Orchestrator controls flow |
| **State** | Framework manages history | Neo4j manages all state |
| **Lifecycle** | Agent persists | Agent instantiated per task |
| **Architecture** | Agent-centric | Graph-centric |

---

## Common Patterns

### Pattern 1: Single-Shot Compilation

```python
def compile(fingerprint: Fingerprint) -> ActionGraph:
    context = assemble_context(fingerprint)
    agent = create_actor_agent()  # Fresh instance
    result = agent(context, structured_output_model=ActionGraph)
    graph_repo.save(result.structured_output)
    return result.structured_output  # Agent discarded
```

### Pattern 2: Actor/Critic Loop

```python
def compile_with_validation(fingerprint: Fingerprint) -> ActionGraph:
    actor = create_actor_agent()
    critic = create_critic_agent()
    context = assemble_context(fingerprint)

    for _ in range(MAX_ITERATIONS):
        action_graph = actor(context, structured_output_model=ActionGraph).structured_output
        feedback = critic(action_graph, structured_output_model=CriticFeedback).structured_output

        if feedback.passed:
            graph_repo.save(action_graph)
            return action_graph

        context += f"\nFeedback: {feedback.feedback}"

    raise CompilationFailedException()
```

### Pattern 3: Self-Repair

```python
def repair(failed_step: Step, error_log: str) -> Step:
    context = assemble_repair_context(failed_step, error_log)
    agent = create_repair_agent()

    diagnosis = agent(
        context,
        structured_output_model=RepairDiagnosis
    ).structured_output

    if diagnosis.failure_type == "systemic":
        # LLM repairs graph
        repaired = agent(
            f"Fix step: {failed_step.command}\nError: {error_log}",
            structured_output_model=Step
        ).structured_output

        graph_repo.create_repair_edge(failed_step, repaired, diagnosis.reason)
        return repaired

    # Transient: retry or restart
    return failed_step
```

---

## Integration with Neo4j

**See `neo4jSchema.md` for complete Neo4j schema, Cypher queries, and GraphRepository implementation details.**

### Tool → Repository → Graph

**Every Strands tool queries Neo4j via GraphRepository:**

```python
from strands import tool

@tool
def find_similar_action_graphs(description: str, top_k: int = 5) -> str:
    """Find ActionGraphs for targets similar to the one described.

    Args:
        description: Natural language description of target characteristics
        top_k: Number of similar results to return
    """
    # 1. Generate embedding
    embedding = embedding_model.encode(description)

    # 2. Query Neo4j via GraphRepository (NOT direct Cypher)
    similar = graph_repo.find_similar_fingerprints(embedding, top_k)

    # 3. Format for LLM consumption
    return format_similar_results(similar)

# GraphRepository implementation (in llmitm/repository/graph_repository.py)
class GraphRepository:
    def find_similar_fingerprints(
        self,
        embedding: list[float],
        top_k: int
    ) -> list[dict]:
        """Execute vector similarity search in Neo4j."""
        query = """
        CALL db.index.vector.queryNodes(
            'fingerprintEmbeddings',
            $top_k,
            $embedding
        )
        YIELD node AS fingerprint, score
        MATCH (fingerprint)-[:TRIGGERS]->(ag:ActionGraph)-[:STARTS_WITH]->(:Step)-[:NEXT*0..50]->(s:Step)
        WITH fingerprint, ag, score, s ORDER BY s.order
        RETURN
            fingerprint {.*, score: score},
            ag {.*},
            collect(s {.*}) AS steps
        """
        with self.driver.session() as session:
            result = session.execute_read(
                lambda tx: tx.run(query, embedding=embedding, top_k=top_k).data()
            )
            return result
```

**Flow:**
```
LLM → @tool function → GraphRepository → Neo4j Driver → Cypher → Graph → Result → Formatted Text → LLM
```

**Four-Layer Retrieval Pipeline:**
1. **Vector search** — Semantic similarity via HNSW index
2. **Graph traversal** — Follow `[:TRIGGERS]` → `[:STARTS_WITH]` → `[:NEXT]` relationships
3. **Business logic** — Format results for LLM consumption
4. **Persona rerank** — LLM decides which result is most relevant

---

### Structured Output → Graph Storage

**Pattern:** LLM generates Pydantic model → GraphRepository serializes to Neo4j:

```python
from strands import Agent
from pydantic import BaseModel, Field

# Pydantic model (serves as contract)
class ActionGraph(BaseModel):
    vulnerability_type: str = Field(description="Type of vulnerability tested")
    description: str = Field(description="Human-readable explanation")
    steps: List[Step] = Field(description="Ordered list of CAMRO steps")

# Agent compilation
actor_agent = Agent(
    model="claude-sonnet-4-5",
    system_prompt="You are a security testing compiler...",
    tools=[find_similar_action_graphs]
)

result = actor_agent(
    prompt=compilation_context,
    structured_output_model=ActionGraph
)

# Extract validated Pydantic object
action_graph: ActionGraph = result.structured_output

# Persist to Neo4j via GraphRepository
graph_repo.save_action_graph(fingerprint, action_graph)
```

**GraphRepository Serialization:**

```python
class GraphRepository:
    def save_action_graph(
        self,
        fingerprint: Fingerprint,
        action_graph: ActionGraph
    ) -> None:
        """Convert Pydantic model to Neo4j nodes/relationships."""
        query = """
        MATCH (f:Fingerprint {hash: $fingerprint_hash})
        CREATE (ag:ActionGraph {
            id: $ag_id,
            vulnerability_type: $vulnerability_type,
            description: $description,
            confidence: $confidence,
            times_executed: 0,
            times_succeeded: 0,
            created_at: datetime()
        })
        CREATE (f)-[:TRIGGERS]->(ag)

        WITH ag
        UNWIND $steps AS step_data
        CREATE (s:Step {
            order: step_data.order,
            phase: step_data.phase,
            type: step_data.type,
            command: step_data.command,
            parameters: step_data.parameters,
            success_criteria: step_data.success_criteria,
            deterministic: step_data.deterministic
        })
        CREATE (ag)-[:HAS_STEP]->(s)

        // Link steps in chain
        WITH ag, collect(s) AS steps
        UNWIND range(0, size(steps) - 2) AS i
        WITH steps[i] AS current, steps[i+1] AS next
        CREATE (current)-[:NEXT]->(next)

        // Set entry point
        WITH ag, steps
        WHERE size(steps) > 0
        CREATE (ag)-[:STARTS_WITH]->(steps[0])
        """

        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    query,
                    fingerprint_hash=fingerprint.hash,
                    ag_id=action_graph.id,
                    vulnerability_type=action_graph.vulnerability_type,
                    description=action_graph.description,
                    confidence=action_graph.confidence,
                    steps=[step.dict() for step in action_graph.steps]
                )
            )
```

**Complete Flow:**
```
Compilation Context (Neo4j) → Agent Call → Pydantic Validation → GraphRepository.save_action_graph() → Neo4j Storage
```

---

## Summary

**Strands SDK Usage in LLMitM v2:**

✅ **What We Use:**
- `Agent` as single-shot compiler
- `structured_output_model` for validation
- `@tool` for graph queries
- `NullConversationManager` for stateless calls
- `SequentialToolExecutor` for dependencies
- `BeforeToolCallEvent` hook for approval

❌ **What We Don't Use:**
- `SessionManager` (Neo4j is state)
- `AgentState` (state lives in graph)
- `SlidingWindowConversationManager` (explicit context)
- Multi-agent patterns (single orchestrator)
- Persistent agent loops (single-shot only)

**Result:** A graph-native, deterministic security testing system where Strands is a precision tool for LLM compilation, not the architectural foundation.

---

**Update Frequency**: After adding new Strands features, tools, or hooks
