# Strands Agents SDK: Interrupts and Observability

This report provides a comprehensive technical overview of the interrupt system and observability features within the Strands Agents SDK for Python. The information is based on the official Strands Agents documentation [1][2][3].

## 1. Interrupts

The interrupt system in the Strands Agents SDK is a powerful feature that facilitates human-in-the-loop workflows. It allows for the pausing of an agent's execution to solicit human input before proceeding. This capability is crucial for scenarios requiring user approval, verification, or interactive guidance.

### 1.1. Raising Interrupts

Interrupts can be triggered from two primary locations within the agent's lifecycle:

*   **Hook Callbacks:** Specifically, the `BeforeToolCallEvent` can be intercepted to raise an interrupt. This is useful for implementing approval flows before a tool is executed.
*   **Tool Definitions:** Interrupts can also be raised directly from within a tool's implementation, allowing for interactive tool execution.

### 1.2. Key Components and Classes

The interrupt mechanism is built around a few key components and classes:

| Component/Class                      | Import Path                          | Description                                                                                                                              |
| ------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `BeforeToolCallEvent`                | `strands.hooks`                      | An event that is triggered before a tool is called, which can be used to raise an interrupt.                                             |
| `HookProvider`                       | `strands.hooks`                      | A base class for creating custom hooks that can respond to events like `BeforeToolCallEvent`.                                            |
| `HookRegistry`                       | `strands.hooks`                      | A registry for adding callbacks to specific events.                                                                                      |
| `ToolContext`                        | `strands.types.tools`                | An object passed to tools that provides context and allows for raising interrupts from within a tool.                                  |
| `FileSessionManager`                 | `strands.session`                    | A session manager that allows for the persistence of interrupt states across different agent sessions.                                   |

### 1.3. Code Examples

#### 1.3.1. Interrupt from a Hook

```python
import json
from typing import Any

from strands import Agent, tool
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


@tool
def delete_files(paths: list[str]) -> bool:
    # Implementation here
    pass


class ApprovalHook(HookProvider):
    def __init__(self, app_name: str) -> None:
        self.app_name = app_name

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.approve)

    def approve(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] != "delete_files":
            return

        approval = event.interrupt(f"{self.app_name}-approval", reason={"paths": event.tool_use["input"]["paths"]})
        if approval.lower() != "y":
            event.cancel_tool = "User denied permission to delete files"
```

#### 1.3.2. Interrupt from a Tool

```python
from typing import Any

from strands import Agent, tool
from strands.types.tools import ToolContext


class DeleteTool:
    def __init__(self, app_name: str) -> None:
        self.app_name = app_name

    @tool(context=True)
    def delete_files(self, tool_context: ToolContext, paths: list[str]) -> bool:
        approval = tool_context.interrupt(f"{self.app_name}-approval", reason={"paths": paths})
        if approval.lower() != "y":
            return False

        # Implementation here

        return True
```

## 2. Observability

The Strands Agents SDK includes a comprehensive observability stack built upon the OpenTelemetry standard. This allows developers to monitor, debug, and analyze the behavior of their agents in a standardized way.

### 2.1. Telemetry Primitives

The observability features are centered around three core telemetry primitives:

*   **Traces:** Provide a detailed, end-to-end view of a request's journey through the agent, including all tool calls and model interactions.
*   **Metrics:** Offer quantitative measurements of the agent's performance, such as token usage, execution time, and error rates.
*   **Logs:** Capture timestamped records of events, which are invaluable for debugging and understanding the agent's internal state.

### 2.2. OpenTelemetry Integration

To enable OpenTelemetry integration, the SDK must be installed with the `[otel]` extra:

```bash
pip install 'strands-agents[otel]'
```

Configuration can be managed through environment variables (e.g., `OTEL_EXPORTER_OTLP_ENDPOINT`) or programmatically using the `StrandsTelemetry` class.

### 2.3. Key Components and Classes

| Component/Class                      | Import Path                          | Description                                                                                                                              |
| ------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `StrandsTelemetry`                   | `strands.telemetry`                  | The main class for configuring and managing OpenTelemetry integration.                                                                   |
| `TelemetryConfig`                    | `strands.telemetry`                  | A configuration object for the `StrandsTelemetry` class.                                                                                 |
| `AgentResult`                        | `strands.agent.agent_result`         | The result object returned by an agent invocation, which contains detailed metrics about the execution.                                  |
| `EventLoopMetrics`                   | `strands.telemetry.metrics`          | A class that holds performance metrics for an agent's event loop.                                                                        |

### 2.4. Code Examples

#### 2.4.1. Configuring Tracing

```python
from strands import Agent
from strands.telemetry import StrandsTelemetry, TelemetryConfig

telemetry = StrandsTelemetry(
    config=TelemetryConfig(
        exporter_config={"endpoint": "http://localhost:4318"}
    )
)

agent = Agent(
    telemetry=telemetry,
    model="us.anthropic.claude-sonnet-4-20250514-v1:0",
    system_prompt="You are a helpful AI assistant"
)
```

#### 2.4.2. Accessing Metrics

```python
from strands import Agent
from strands_tools import calculator

agent = Agent(tools=[calculator])
result = agent("What is the square root of 144?")

print(f"Total tokens: {result.metrics.accumulated_usage['totalTokens']}")
print(f"Execution time: {sum(result.metrics.cycle_durations):.2f} seconds")
```

#### 2.4.3. Configuring Logging

```python
import logging

logging.getLogger("strands").setLevel(logging.DEBUG)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
```

## 3. Conclusion

The Strands Agents SDK provides a robust and well-designed framework for building interactive and observable AI agents. The interrupt system enables complex human-in-the-loop workflows, while the OpenTelemetry-based observability stack offers deep insights into agent performance and behavior. By leveraging these features, developers can create more reliable, transparent, and effective agents.

## References

[1]: Strands Agents Documentation - Interrupts. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/interrupts/index.md
[2]: Strands Agents Documentation - Observability. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/observability/index.md
[3]: Strands Agents Documentation - Traces. (n.d.). Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/traces/index.md
