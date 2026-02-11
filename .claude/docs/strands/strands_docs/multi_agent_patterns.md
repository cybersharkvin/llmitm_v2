# Strands Multi-Agent Patterns: A Technical Research Report

This report provides a comprehensive overview of the multi-agent patterns available in the Strands Agents SDK for Python. It covers the core concepts of multi-agent systems and delves into the specifics of the Graph, Swarm, and Workflow patterns. The information is based on the official Strands Agents documentation [1][2][3].

## Core Concepts of Multi-Agent Systems

Multi-agent systems in Strands are built on three core principles:

*   **Orchestration**: A controlling logic or structure is used to manage the flow of information and tasks between agents.
*   **Specialization**: Each agent has a specific role, expertise, and a set of tools it can use to perform its tasks.
*   **Collaboration**: Agents communicate and share information to work together towards a common goal.

## Multi-Agent Patterns at a Glance

The Strands Agents SDK offers three primary patterns for orchestrating multi-agent systems: Graph, Swarm, and Workflow. The following table provides a high-level comparison of these patterns:

| Feature | Graph | Swarm | Workflow |
| --- | --- | --- | --- |
| **Core Concept** | A structured, developer-defined flowchart where an agent decides which path to take. | A dynamic, collaborative team of agents that autonomously hand off tasks. | A pre-defined Task Graph (DAG) executed as a single, non-conversational tool. |
| **Structure** | The developer defines all nodes (agents) and edges (transitions) in advance. | The developer provides a pool of agents, and the agents themselves decide the execution path. | The developer defines all tasks and their dependencies in code. |
| **Execution Flow** | The flow is controlled but dynamic, following graph edges based on an LLM's decision at each node. | The execution is sequential and autonomous, with agents handing off control to peers. | The flow is deterministic and can be parallel, fixed by the dependency graph. |
| **Cycles** | Cycles are allowed, enabling iterative workflows. | Cycles are allowed, with safeguards to prevent infinite loops. | Cycles are not allowed as it is a Directed Acyclic Graph (DAG). |
| **State Sharing** | A single, shared dictionary object is passed to all agents. | A "shared context" or working memory is available to all agents. | The tool automatically captures task outputs and passes them as inputs to dependent tasks. |
| **Conversation History** | The entire dialogue history is available to every agent. | A shared transcript of agent handoffs and knowledge is available to the current agent. | A task receives a curated summary of relevant results from its dependencies. |
| **Error Handling** | Controllable, with the ability to define explicit error-handling nodes. | Agent-driven, where an agent can hand off to a specialist for error handling. | Systemic, where a failure in one task halts all downstream dependent tasks. |

---

## The Graph Pattern

The **Graph** pattern in Strands provides a way to create structured, deterministic workflows for multi-agent systems. It uses a directed graph where nodes represent agents or other multi-agent systems, and edges define the dependencies and flow of information between them. This pattern is ideal for processes that require conditional logic, branching, and predictable execution paths.

### Key Components

The Graph pattern is built upon three main components:

*   `GraphNode`: This class represents a single node within the graph. Each `GraphNode` has a unique `node_id`, an `executor` (which is an `Agent` or `MultiAgentBase` instance), a set of `dependencies`, and tracks its `execution_status` and `result`.

*   `GraphEdge`: This represents a connection between two nodes, defining the direction of control flow. An edge is defined by its `from_node` and `to_node`. Crucially, a `GraphEdge` can have a `condition` function that determines whether the edge should be traversed, allowing for dynamic routing.

*   `GraphBuilder`: This utility class provides a fluent API for constructing a `Graph`. It includes methods like `add_node()`, `add_edge()`, `set_entry_point()`, and `build()` to assemble the graph structure. It also allows for configuring execution parameters such as timeouts and execution limits, which is particularly important for cyclic graphs.

### Code Example: Building a Research Agent Graph

The following code demonstrates how to construct and execute a simple graph of agents for a research task. A `researcher` agent gathers information, which is then passed to an `analyst` and a `fact_checker` in parallel. Finally, a `report_writer` agent consolidates the outputs to produce the final report.

```python
import logging
from strands import Agent
from strands.multiagent import GraphBuilder

# Configure logging
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define specialized agents
researcher = Agent(name="researcher", system_prompt="You are a research specialist...")
analyst = Agent(name="analyst", system_prompt="You are a data analysis specialist...")
fact_checker = Agent(name="fact_checker", system_prompt="You are a fact checking specialist...")
report_writer = Agent(name="report_writer", system_prompt="You are a report writing specialist...")

# Use GraphBuilder to construct the graph
builder = GraphBuilder()
builder.add_node(researcher, "research")
builder.add_node(analyst, "analysis")
builder.add_node(fact_checker, "fact_check")
builder.add_node(report_writer, "report")

# Define the execution flow with edges
builder.add_edge("research", "analysis")
builder.add_edge("research", "fact_check")
builder.add_edge("analysis", "report")
builder.add_edge("fact_check", "report")

# Set the entry point and execution limits
builder.set_entry_point("research")
builder.set_execution_timeout(600)  # 10-minute timeout

# Build and execute the graph
graph = builder.build()
result = graph("Research the impact of AI on healthcare and create a comprehensive report")

print(f"\nStatus: {result.status}")
print(f"Execution order: {[node.node_id for node in result.execution_order]}")
```

### Advanced Control Flow

A key feature of the Graph pattern is the ability to control the flow of execution using conditional edges. A `condition` function can be attached to an edge to determine if it should be traversed based on the current state of the graph. This allows for implementing complex logic, such as waiting for multiple dependencies to complete before proceeding.

```python
from strands.multiagent.graph import GraphState
from strands.multiagent.base import Status

def all_dependencies_complete(required_nodes: list[str]):
    """Factory to create a condition that checks if all specified nodes have completed."""
    def check_all_complete(state: GraphState) -> bool:
        return all(
            node_id in state.results and state.results[node_id].status == Status.COMPLETED
            for node_id in required_nodes
        )
    return check_all_complete

# The 'Z' node will only execute after 'A', 'B', and 'C' have all completed.
condition = all_dependencies_complete(["A", "B", "C"])
builder.add_edge("A", "Z", condition=condition)
builder.add_edge("B", "Z", condition=condition)
builder.add_edge("C", "Z", condition=condition)
```

---

## The Swarm Pattern

The **Swarm** pattern offers a more dynamic and collaborative approach to multi-agent orchestration. In a Swarm, a team of specialized agents works together to solve a problem, but the execution path is not predetermined. Instead, agents autonomously decide when to hand off the task to another agent with the required expertise. This pattern is well-suited for complex problems where the solution path is not known in advance and requires the collective intelligence of multiple agents.

### How Swarms Work

Swarms are based on the principle of emergent intelligence. Each agent in the swarm has access to a shared context, which includes the original task, the history of agent handoffs, and any knowledge contributed by previous agents. This shared understanding allows agents to make informed decisions about when to contribute and when to pass the task to a more suitable peer. This is facilitated by a `handoff_to_agent` tool that is automatically provided to each agent in the swarm.

### Key Components

The primary component of the Swarm pattern is the `Swarm` class itself. When creating a `Swarm`, you provide a list of `Agent` instances, each with its own specialization. You can also configure various parameters to control the swarm's behavior, such as:

*   `entry_point`: The agent that will receive the initial task.
*   `max_handoffs`: The maximum number of times the task can be passed between agents.
*   `execution_timeout`: A timeout for the entire swarm execution.
*   `node_timeout`: A timeout for each individual agent's execution.

### Code Example: A Collaborative Development Team

The following example illustrates how to create a swarm of agents that collaborate to design and implement a REST API. The task is initially given to the `researcher`, who can then hand it off to the `architect`, `coder`, and `reviewer` as needed.

```python
import logging
from strands import Agent
from strands.multiagent import Swarm

# Configure logging
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define specialized agents
researcher = Agent(name="researcher", system_prompt="You are a research specialist...")
coder = Agent(name="coder", system_prompt="You are a coding specialist...")
reviewer = Agent(name="reviewer", system_prompt="You are a code review specialist...")
architect = Agent(name="architect", system_prompt="You are a system architecture specialist...")

# Create the swarm
swarm = Swarm(
    [coder, researcher, reviewer, architect],
    entry_point=researcher,
    max_handoffs=20,
    execution_timeout=900.0,  # 15 minutes
)

# Execute the swarm
result = swarm("Design and implement a simple REST API for a todo app")

print(f"Status: {result.status}")
print(f"Node history: {[node.node_id for node in result.node_history]}")
```

---

## The Workflow Pattern

The **Workflow** pattern provides a way to execute a pre-defined sequence of tasks as a single, non-conversational tool. It is essentially a Directed Acyclic Graph (DAG) of tasks, where the output of one task is automatically passed as input to its dependent tasks. This pattern is best for repeatable, complex operations where the sequence of tasks is known and does not require dynamic decision-making at runtime.

### How Workflows Differ from Graphs

While both Workflows and Graphs are based on a graph structure, they serve different purposes. A `Graph` is designed for conversational and dynamic workflows, where an LLM's decision at each node can alter the execution path. In contrast, a `Workflow` is a static, non-conversational tool that executes a predefined sequence of tasks. It is not designed for back-and-forth interaction with a user.

### Key Characteristics

*   **Deterministic Execution**: The execution order is fixed by the dependencies defined in the workflow.
*   **Parallelism**: Independent tasks in the workflow can be executed in parallel, leading to efficient resource utilization.
*   **No Cycles**: As a DAG, workflows do not support cycles or feedback loops.
*   **Task-Specific Context**: Each task in the workflow receives only the outputs of its direct dependencies, not the full history of the workflow.

---

## Key Classes and Interfaces

The following are the key classes and interfaces involved in the multi-agent patterns discussed:

*   `strands.agent.Agent`: The fundamental building block for creating specialized agents.
*   `strands.multiagent.base.MultiAgentBase`: The abstract base class for all multi-agent systems.
*   `strands.multiagent.graph.Graph`: The class that represents a graph-based multi-agent system.
*   `strands.multiagent.graph.GraphBuilder`: A helper class for constructing `Graph` instances.
*   `strands.multiagent.graph.GraphNode`: Represents a node within a `Graph`.
*   `strands.multiagent.graph.GraphEdge`: Represents an edge between nodes in a `Graph`.
*   `strands.multiagent.graph.GraphState`: Represents the state of the graph at a given time.
*   `strands.multiagent.swarm.Swarm`: The class that represents a swarm-based multi-agent system.
*   `strands.multiagent.base.Status`: An enum representing the execution status of a node or system.

## Code Examples

This section provides the complete code examples for the patterns discussed in this report.

### Graph Pattern: Research Agent Graph

```python
import logging
from strands import Agent
from strands.multiagent import GraphBuilder

# Configure logging
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define specialized agents
researcher = Agent(name="researcher", system_prompt="You are a research specialist...")
analyst = Agent(name="analyst", system_prompt="You are a data analysis specialist...")
fact_checker = Agent(name="fact_checker", system_prompt="You are a fact checking specialist...")
report_writer = Agent(name="report_writer", system_prompt="You are a report writing specialist...")

# Use GraphBuilder to construct the graph
builder = GraphBuilder()
builder.add_node(researcher, "research")
builder.add_node(analyst, "analysis")
builder.add_node(fact_checker, "fact_check")
builder.add_node(report_writer, "report")

# Define the execution flow with edges
builder.add_edge("research", "analysis")
builder.add_edge("research", "fact_check")
builder.add_edge("analysis", "report")
builder.add_edge("fact_check", "report")

# Set the entry point and execution limits
builder.set_entry_point("research")
builder.set_execution_timeout(600)  # 10-minute timeout

# Build and execute the graph
graph = builder.build()
result = graph("Research the impact of AI on healthcare and create a comprehensive report")

print(f"\nStatus: {result.status}")
print(f"Execution order: {[node.node_id for node in result.execution_order]}")
```

### Graph Pattern: Conditional Edges

```python
from strands.multiagent.graph import GraphState
from strands.multiagent.base import Status

def all_dependencies_complete(required_nodes: list[str]):
    """Factory to create a condition that checks if all specified nodes have completed."""
    def check_all_complete(state: GraphState) -> bool:
        return all(
            node_id in state.results and state.results[node_id].status == Status.COMPLETED
            for node_id in required_nodes
        )
    return check_all_complete

# The 'Z' node will only execute after 'A', 'B', and 'C' have all completed.
condition = all_dependencies_complete(["A", "B", "C"])
builder.add_edge("A", "Z", condition=condition)
builder.add_edge("B", "Z", condition=condition)
builder.add_edge("C", "Z", condition=condition)
```

### Swarm Pattern: Collaborative Development Team

```python
import logging
from strands import Agent
from strands.multiagent import Swarm

# Configure logging
logging.getLogger("strands.multiagent").setLevel(logging.DEBUG)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define specialized agents
researcher = Agent(name="researcher", system_prompt="You are a research specialist...")
coder = Agent(name="coder", system_prompt="You are a coding specialist...")
reviewer = Agent(name="reviewer", system_prompt="You are a code review specialist...")
architect = Agent(name="architect", system_prompt="You are a system architecture specialist...")

# Create the swarm
swarm = Swarm(
    [coder, researcher, reviewer, architect],
    entry_point=researcher,
    max_handoffs=20,
    execution_timeout=900.0,  # 15 minutes
)

# Execute the swarm
result = swarm("Design and implement a simple REST API for a todo app")

print(f"Status: {result.status}")
print(f"Node history: {[node.node_id for node in result.node_history]}")
```

## References

[1] Strands Agents Documentation - Multi-Agent Patterns. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/index.md

[2] Strands Agents Documentation - Graph. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/graph/index.md

[3] Strands Agents Documentation - Workflow. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/workflow/index.md

[4] Strands Agents Documentation - Swarm. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/index.md
