# Strands Hooks System Technical Research Report

This report provides a comprehensive overview of the Strands Hooks System, based on the official Strands Agents SDK documentation. It covers the core concepts, usage patterns, and advanced features of the hooks system.

## 1. Key Findings

The Strands Hooks System is a powerful and composable extensibility mechanism that allows developers to subscribe to events throughout the agent lifecycle. This enables the injection of custom logic for a variety of purposes, including monitoring, behavior modification, and enhanced error handling. The system is designed to be type-safe and supports multiple subscribers for each event type, ensuring both flexibility and robustness.

### 1.1. Core Concepts

- **Hook Event**: A specific, well-defined event that occurs during the agent's lifecycle. Examples include `BeforeInvocationEvent` and `AfterToolCallEvent`.
- **Hook Callback**: A function that is registered to a specific hook event and is executed when that event is emitted. Callbacks receive a strongly-typed event object containing relevant contextual data.

### 1.2. Registering Hooks

Hooks can be registered in two primary ways:

1.  **Individual Callbacks**: For simple cases, a single callback function can be directly registered to an event type using the `agent.hooks.add_callback()` method.
2.  **HookProvider**: For more complex scenarios, the `HookProvider` protocol allows for the encapsulation of multiple related hooks within a single class. This class implements a `register_hooks` method that receives a `HookRegistry` object for registering callbacks. `HookProvider` instances can be passed to the `Agent` constructor or added later using `agent.hooks.add_hook()`.

### 1.3. Event Lifecycle

The hooks system defines distinct event lifecycles for single-agent and multi-agent scenarios:

- **Single-Agent Lifecycle**: This lifecycle includes events for the start and end of an invocation, model calls, and tool calls.
- **Multi-Agent Lifecycle**: In addition to the single-agent events, the multi-agent lifecycle includes events for the initialization of the orchestrator and the execution of individual nodes within the graph.

### 1.4. Available Events

The following table summarizes the available hook events:

| Event | Description |
| --- | --- |
| `AgentInitializedEvent` | Triggered when an agent has been constructed and finished initialization. |
| `BeforeInvocationEvent` | Triggered at the beginning of a new agent invocation request. |
| `AfterInvocationEvent` | Triggered at the end of an agent request, regardless of success or failure. |
| `MessageAddedEvent` | Triggered when a message is added to the agent's conversation history. |
| `BeforeModelCallEvent` | Triggered before the model is invoked for inference. |
| `AfterModelCallEvent` | Triggered after model invocation completes. |
| `BeforeToolCallEvent` | Triggered before a tool is invoked. |
| `AfterToolCallEvent` | Triggered after tool invocation completes. |
| `MultiAgentInitializedEvent` | (Python only) Triggered when a multi-agent orchestrator is initialized. |
| `BeforeMultiAgentInvocationEvent` | (Python only) Triggered before orchestrator execution starts. |
| `AfterMultiAgentInvocationEvent` | (Python only) Triggered after orchestrator execution completes. |
| `BeforeNodeCallEvent` | (Python only) Triggered before individual node execution starts. |
| `AfterNodeCallEvent` | (Python only) Triggered after individual node execution completes. |

### 1.5. Modifying Agent Behavior

Certain event properties can be modified within a hook callback to alter the agent's behavior:

- **`AfterModelCallEvent.retry`**: Request a retry of the model invocation.
- **`BeforeToolCallEvent.cancel_tool`**: Cancel the execution of a tool.
- **`BeforeToolCallEvent.selected_tool`**: Replace the tool to be executed.
- **`BeforeToolCallEvent.tool_use`**: Modify the parameters of a tool before execution.
- **`AfterToolCallEvent.result`**: Modify the result of a tool after execution.

### 1.6. Advanced Usage

The hooks system enables several advanced usage patterns:

- **Accessing Invocation State**: Hooks can access a shared `invocation_state` dictionary to read contextual data, such as user IDs, session information, or even non-serializable objects like database connections.
- **Tool Interception and Result Modification**: Hooks can intercept tool calls to modify their parameters or even replace the tool entirely. They can also modify the results of tool calls.
- **Conditional Node Execution**: In multi-agent systems, hooks can be used to implement conditional logic that determines whether a particular node in the graph should be executed.
- **Custom Retry Logic**: The `AfterModelCallEvent.retry` property allows for the implementation of custom retry mechanisms, such as exponential backoff on specific errors.

## 2. Code Examples

### 2.1. Registering an Individual Hook Callback

```python
agent = Agent()

# Register individual callbacks
def my_callback(event: BeforeInvocationEvent) -> None:
    print("Custom callback triggered")

agent.hooks.add_callback(BeforeInvocationEvent, my_callback)
```

### 2.2. Creating a HookProvider

```python
class LoggingHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.log_start)
        registry.add_callback(AfterInvocationEvent, self.log_end)

    def log_start(self, event: BeforeInvocationEvent) -> None:
        print(f"Request started for agent: {event.agent.name}")

    def log_end(self, event: AfterInvocationEvent) -> None:
        print(f"Request completed for agent: {event.agent.name}")

# Passed in via the hooks parameter
agent = Agent(hooks=[LoggingHook()])

# Or added after the fact
agent.hooks.add_hook(LoggingHook())
```

### 2.3. Accessing Invocation State in Hooks

```python
from strands.hooks import BeforeToolCallEvent
import logging

def log_with_context(event: BeforeToolCallEvent) -> None:
    """Log tool invocations with context from invocation state."""
    # Access invocation state from the event
    user_id = event.invocation_state.get("user_id", "unknown")
    session_id = event.invocation_state.get("session_id")

    # Access non-JSON serializable objects like database connections
    db_connection = event.invocation_state.get("database_connection")
    logger_instance = event.invocation_state.get("custom_logger")

    # Use custom logger if provided, otherwise use default
    logger = logger_instance if logger_instance else logging.getLogger(__name__)

    logger.info(
        f"User {user_id} in session {session_id} "
        f"invoking tool: {event.tool_use['name']} "
        f"with args: {event.tool_use['input']}"
    )
```

### 2.4. Fixed Tool Arguments

```python
from strands import tool
from strands.hooks import HookProvider, BeforeToolCallEvent

@tool
def calculator(operation: str, a: int, b: int) -> int:
    """Performs a calculation and returns the result."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b

class FixCalculator(HookProvider):
    """Forces the calculator to always use the divide operation."""

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self.fix_calculator)

    def fix_calculator(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] == "calculator":
            event.tool_use["input"]["operation"] = "divide"

fix_parameters = FixCalculator()

agent = Agent(tools=[calculator], hooks=[fix_parameters])
result = agent("What is 2 / 3?")
```

### 2.5. Limit Tool Counts

```python
from strands import tool
from strands.hooks import HookRegistry, HookProvider, BeforeToolCallEvent, BeforeInvocationEvent
from threading import Lock

class LimitToolCounts(HookProvider):
    """Limits the number of times tools can be called per agent invocation"""

    def __init__(self, max_tool_counts: dict[str, int]):
        """
        Initializer.

        Args:
            max_tool_counts: A dictionary mapping tool names to max call counts for 
                tools. If a tool is not specified in it, the tool can be called as many
                times as desired
        """
        self.max_tool_counts = max_tool_counts
        self.tool_counts = {}
        self._lock = Lock()

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset_counts)
        registry.add_callback(BeforeToolCallEvent, self.intercept_tool)

    def reset_counts(self, event: BeforeInvocationEvent) -> None:
        with self._lock:
            self.tool_counts = {}

    def intercept_tool(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use["name"]
        with self._lock:
            max_tool_count = self.max_tool_counts.get(tool_name)
            tool_count = self.tool_counts.get(tool_name, 0) + 1
            self.tool_counts[tool_name] = tool_count

        if max_tool_count and tool_count > max_tool_count:
            event.cancel_tool = (
                f"Tool '{tool_name}' has been invoked too many and is now being throttled. "
                f"DO NOT CALL THIS TOOL ANYMORE "
            )

limit_hook = LimitToolCounts(max_tool_counts={"sleep": 3})

agent = Agent(tools=[sleep], hooks=[limit_hook])

# This call will only have 3 successful sleeps
agent("Sleep 5 times for 10ms each or until you can't anymore")
# This will sleep successfully again because the count resets every invocation
agent("Sleep once")
```

### 2.6. Model Call Retry

```python
import asyncio
import logging
from strands.hooks import HookProvider, HookRegistry, BeforeInvocationEvent, AfterModelCallEvent

logger = logging.getLogger(__name__)

class RetryOnServiceUnavailable(HookProvider):
    """Retry model calls when ServiceUnavailable errors occur."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_count = 0

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset_counts)
        registry.add_callback(AfterModelCallEvent, self.handle_retry)

    def reset_counts(self, event: BeforeInvocationEvent = None) -> None:
        self.retry_count = 0

    async def handle_retry(self, event: AfterModelCallEvent) -> None:
        if event.exception:
            if "ServiceUnavailable" in str(event.exception):
                logger.info("ServiceUnavailable encountered")
                if self.retry_count < self.max_retries:
                    logger.info("Retrying model call")
                    self.retry_count += 1
                    event.retry = True
                    await asyncio.sleep(2 ** self.retry_count)  # Exponential backoff
        else:
            # Reset counts on successful call
            self.reset_counts()

from strands import Agent

retry_hook = RetryOnServiceUnavailable(max_retries=3)
agent = Agent(hooks=[retry_hook])

result = agent("What is the capital of France?")
```

## 3. Classes and Interfaces

The following are the key classes, protocols, and their import paths as identified from the documentation:

- `strands.hooks.HookProvider`
- `strands.hooks.HookRegistry`
- `strands.hooks.events.AgentInitializedEvent`
- `strands.hooks.events.BeforeInvocationEvent`
- `strands.hooks.events.AfterInvocationEvent`
- `strands.hooks.events.MessageAddedEvent`
- `strands.hooks.events.BeforeModelCallEvent`
- `strands.hooks.events.AfterModelCallEvent`
- `strands.hooks.events.BeforeToolCallEvent`
- `strands.hooks.events.AfterToolCallEvent`
- `strands.hooks.events.MultiAgentInitializedEvent`
- `strands.hooks.events.BeforeMultiAgentInvocationEvent`
- `strands.hooks.events.AfterMultiAgentInvocationEvent`
- `strands.hooks.events.BeforeNodeCallEvent`
- `strands.hooks.events.AfterNodeCallEvent`

## References

[1] [Strands Agents SDK — Hooks](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/hooks/index.md)
[2] [Strands Agents SDK — Agent Class](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-class/index.md)
[3] [Strands Agents SDK — Multi-Agent Hooks](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/index.md)
