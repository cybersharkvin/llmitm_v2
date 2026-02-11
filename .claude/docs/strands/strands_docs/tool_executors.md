# Strands Tool Executors: A Technical Research Report

## 1. Introduction

Tool executors within the Strands SDK for Python provide a mechanism for developers to define the execution strategy for tools called by an agent. This allows for control over whether tools are run sequentially or concurrently, which has significant implications for performance and dependency management. This report details the available tool executors, their configuration, and usage patterns based on the official Strands documentation [1].

## 2. Execution Strategies

The Strands SDK currently offers two primary tool execution strategies, each implemented as a distinct executor class.

### 2.1. Concurrent Execution

The `ConcurrentToolExecutor` is the default execution strategy in the Strands SDK. It is designed to execute tools concurrently, which can lead to significant performance improvements when an agent needs to call multiple independent tools in response to a prompt. Concurrency is achieved only when the underlying language model returns multiple tool use requests in a single response. If the model returns tool requests one at a time, they will be executed sequentially even with the `ConcurrentToolExecutor`.

### 2.2. Sequential Execution

The `SequentialToolExecutor` provides a strictly sequential execution strategy. When this executor is used, tools are executed one after another in the exact order they are returned by the language model. This is useful in scenarios where there is an explicit dependency between tools, such as taking a screenshot and then emailing it.

## 3. Configuration

To use a specific tool executor, you must pass an instance of the desired executor class to the `tool_executor` parameter of the `Agent` class constructor. If the `tool_executor` parameter is not provided, the agent will default to using the `ConcurrentToolExecutor`.

## 4. Code Examples

The following code examples illustrate how to configure and use both the concurrent and sequential tool executors.

### 4.1. ConcurrentToolExecutor Example

```python
from strands import Agent
from strands.tools.executors import ConcurrentToolExecutor

# Explicitly configure the agent to use the ConcurrentToolExecutor
agent = Agent(
    tool_executor=ConcurrentToolExecutor(),
    tools=[weather_tool, time_tool]
)

# This is equivalent to the default behavior
# agent = Agent(tools=[weather_tool, time_tool])

# The weather_tool and time_tool will be executed concurrently
agent("What is the weather and time in New York?")
```

### 4.2. SequentialToolExecutor Example

```python
from strands import Agent
from strands.tools.executors import SequentialToolExecutor

# Configure the agent to use the SequentialToolExecutor
agent = Agent(
    tool_executor=SequentialToolExecutor(),
    tools=[screenshot_tool, email_tool]
)

# The screenshot_tool will execute first, followed by the email_tool
agent("Please take a screenshot and then email the screenshot to my friend")
```

## 5. Classes and Interfaces

The primary classes associated with tool execution are:

*   `strands.tools.executors.ConcurrentToolExecutor`
*   `strands.tools.executors.SequentialToolExecutor`

No abstract base classes or public interfaces for custom executors were identified in the documentation. The documentation notes that custom tool executors are not currently supported but are planned for a future release.

## 6. Key Findings Summary

The research on Strands Tool Executors reveals a straightforward but powerful feature for controlling tool execution flow. The key takeaways are that the SDK provides two modes: concurrent (default) and sequential. The choice of executor is determined at the time of the `Agent`'s instantiation. Concurrent execution is dependent on the model's ability to return multiple tool calls in a single response. Sequential execution is guaranteed when using the `SequentialToolExecutor`. The implementation is simple, requiring only the instantiation of the desired executor class.

## 7. References

[1] Strands Agents. (2026). *Tool Executors*. Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/executors/index.md
