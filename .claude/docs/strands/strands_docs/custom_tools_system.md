# Strands Custom Tools System: A Technical Deep Dive

This report provides a comprehensive overview of the Strands Custom Tools System for the Python SDK, based on the official Strands Agents documentation. It covers the creation, registration, and invocation of custom tools, as well as the core classes and concepts that underpin the system.

## 1. Introduction to Custom Tools

Custom tools are the primary mechanism for extending the capabilities of Strands agents, allowing them to interact with external systems, access data, and perform a wide range of actions beyond simple text generation. The Strands SDK provides a flexible and powerful system for creating and integrating custom tools, which can be implemented as simple decorated functions, class methods, or standalone modules.

## 2. Creating Custom Tools

There are three primary approaches to creating custom tools in the Strands Python SDK:

*   **Decorated Python Functions**: Using the `@tool` decorator to transform regular Python functions into tools.
*   **Class-based Tools**: Defining tools as methods within a class to share state and resources.
*   **Module-based Tools**: Creating tools in separate Python modules with a specific structure.

### 2.1. Using the `@tool` Decorator

The `@tool` decorator is the simplest and most common way to create a custom tool. It automatically extracts metadata from the function's docstring and type hints to generate a tool specification.

**Basic Syntax:**

```python
from strands import tool

@tool
def my_tool(param1: str, param2: int = 42) -> str:
    """Tool description - explain what it does.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter (default: 42).
    """
    return f"Result based on {param1} and {param2}"
```

The decorator uses the first paragraph of the docstring as the tool's description and the `Args` section for parameter descriptions. This information, combined with the function's type hints, is used to create a complete tool specification that the agent can understand.

### 2.2. Overriding Tool Metadata

The `@tool` decorator allows you to override the automatically generated metadata by passing arguments to it:

*   `name`: A string to set a custom tool name.
*   `description`: A string to provide a custom description.
*   `inputSchema`: A JSON schema to define the tool's input parameters, overriding the one generated from type hints and the docstring.

```python
@tool(
    name="custom_tool_name",
    description="A custom description for the tool.",
    inputSchema={
        "json": {
            "type": "object",
            "properties": {
                "custom_param": {"type": "string", "description": "A custom parameter"}
            },
            "required": ["custom_param"]
        }
    }
)
def my_tool(custom_param: str) -> str:
    """Implementation of the tool."""
    return f"Result from {custom_param}"
```

### 2.3. Class-based Tools

For tools that require shared state or resources, you can define them as methods within a class. The `@tool` decorator can be applied to class methods, which then have access to the instance's attributes (`self`).

```python
from strands import tool, Agent

class DatabaseTools:
    def __init__(self, connection_string: str):
        self.connection = self._connect(connection_string)

    def _connect(self, connection_string: str) -> str:
        # Simulate database connection
        return f"Connected to {connection_string}"

    @tool
    def query_database(self, sql: str) -> dict:
        """Run a SQL query against the database.

        Args:
            sql: The SQL query to execute
        """
        # Uses the shared connection
        return {"results": f"Query results for: {sql}", "connection": self.connection}

db_tools = DatabaseTools("example_connection_string")
agent = Agent(tools=[db_tools.query_database])
```

### 2.4. Module-based Tools

Tools can also be defined in separate Python modules. This approach requires two components:

1.  A `TOOL_SPEC` variable containing the tool's specification.
2.  A function with the same name as the tool defined in `TOOL_SPEC`.

```python
# weather_forecast.py
from typing import Any

TOOL_SPEC = {
    "name": "weather_forecast",
    "description": "Get weather forecast for a city.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The name of the city"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days for the forecast",
                    "default": 3
                }
            },
            "required": ["city"]
        }
    }
}

def weather_forecast(tool, **kwargs: Any):
    tool_use_id = tool["toolUseId"]
    tool_input = tool["input"]
    city = tool_input.get("city", "")
    days = tool_input.get("days", 3)
    result = f"Weather forecast for {city} for the next {days} days..."
    return {
        "toolUseId": tool_use_id,
        "status": "success",
        "content": [{"text": result}]
    }
```

## 3. Tool Registration and Loading

Tools can be added to an agent in several ways:

*   **Directly passing tool objects**: Pass a list of tool objects (decorated functions, class methods, or modules) to the `Agent` constructor's `tools` parameter.

    ```python
    from strands import Agent
    from my_tools import my_tool1, my_tool2

    agent = Agent(tools=[my_tool1, my_tool2])
    ```

*   **Loading from file paths**: Pass a list of file paths to the `tools` parameter.

    ```python
    from strands import Agent

    agent = Agent(tools=["./my_tools/tool1.py", "/path/to/another/tool.py"])
    ```

*   **Auto-loading from a directory**: Set `load_tools_from_directory=True` in the `Agent` constructor to automatically load all tools from the `./tools/` directory. This also enables hot-reloading of tools when they are modified.

    ```python
    from strands import Agent

    agent = Agent(load_tools_from_directory=True)
    ```

## 4. Tool Invocation

Tools can be invoked in two ways:

*   **Natural Language Invocation**: The agent automatically determines when to use a tool based on the user's natural language input.
*   **Direct Method Calls**: Tools can be invoked programmatically as methods on the `agent.tool` object. When calling tools directly, you must use keyword arguments.

    ```python
    # Direct invocation
    result = agent.tool.my_tool(param1="value1", param2=123)
    ```

## 5. The `@tool` Decorator API

The `@tool` decorator has the following signature:

```python
tool(
    description: str | None = None,
    inputSchema: JSONSchema | None = None,
    name: str | None = None,
    context: bool | str = False,
) -> Callable[
    [Callable[P, R]], DecoratedFunctionTool[P, R]
]
```

*   `description`: Overrides the tool's description.
*   `inputSchema`: Overrides the tool's input schema.
*   `name`: Overrides the tool's name.
*   `context`: If `True`, injects a `ToolContext` object into the tool's execution. The default parameter name is `tool_context`, but you can provide a string to specify a custom parameter name.

## 6. Tool Context (`ToolContext`)

Tools can access their execution context by setting `context=True` in the `@tool` decorator. This injects a `ToolContext` object, which provides access to:

*   `agent`: The agent instance that invoked the tool.
*   `tool_use`: A dictionary containing the tool use request data.
*   `invocation_state`: A dictionary of state provided by the caller when the agent was invoked.

```python
from strands import tool, ToolContext

@tool(context=True)
def my_contextual_tool(tool_context: ToolContext) -> str:
    agent_name = tool_context.agent.name
    tool_use_id = tool_context.tool_use["toolUseId"]
    return f"Agent '{agent_name}' invoked tool with ID {tool_use_id}"
```

## 7. Tool Response Format (`ToolResult`)

Tools can return a variety of response formats. The `@tool` decorator automatically wraps simple return values (like strings) into a `ToolResult` dictionary. For more complex scenarios, you can return a dictionary that conforms to the `ToolResult` structure:

```python
{
    "toolUseId": str,       # Optional: The ID of the tool use request
    "status": str,          # "success" or "error"
    "content": List[dict]   # A list of content items (e.g., {"text": ...} or {"json": ...})
}
```

## 8. Core Classes and Interfaces

### 8.1. `strands.tools.decorator.AgentTool`

This is the abstract base class for all tools in the Strands SDK. It defines the interface that all tool implementations must follow, including the `tool_name`, `tool_spec`, and `stream` methods.

### 8.2. `strands.tools.decorator.DecoratedFunctionTool`

This class is a wrapper for functions decorated with `@tool`. It adapts the decorated function to the `AgentTool` interface, handling both direct function calls and tool use invocations.

## 9. Code Examples

This section consolidates the Python code examples from the documentation for easy reference.

**Basic Tool:**

```python
from strands import tool

@tool
def weather_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: The name of the city
        days: Number of days for the forecast
    """
    return f"Weather forecast for {city} for the next {days} days..."
```

**Async Tool:**

```python
import asyncio
from strands import Agent, tool

@tool
async def call_api() -> str:
    """Call API asynchronously."""
    await asyncio.sleep(5)  # simulated api call
    return "API result"
```

**Class-based Tool:**

```python
from strands import tool

class DatabaseTools:
    def __init__(self, connection_string: str):
        self.connection = self._connect(connection_string)

    def _connect(self, connection_string: str) -> str:
        return f"Connected to {connection_string}"

    @tool
    def query_database(self, sql: str) -> dict:
        """Run a SQL query against the database.

        Args:
            sql: The SQL query to execute
        """
        return {"results": f"Query results for: {sql}", "connection": self.connection}
```

**Tool with Context:**

```python
from strands import tool, ToolContext

@tool(context=True)
def get_self_name(tool_context: ToolContext) -> str:
    return f"The agent name is {tool_context.agent.name}"
```

## 10. Key Findings Summary

The Strands Custom Tools System is a comprehensive and flexible framework for extending agent capabilities. Key features include:

*   **Multiple creation methods**: Tools can be created from functions, classes, or modules, catering to different use cases and levels of complexity.
*   **Automatic metadata extraction**: The `@tool` decorator simplifies tool creation by automatically generating tool specifications from docstrings and type hints.
*   **State management**: Class-based tools allow for the management of state and shared resources across tool invocations.
*   **Contextual awareness**: The `ToolContext` provides tools with access to the agent, tool use request, and invocation state, enabling more advanced and context-aware tool logic.
*   **Flexible registration and loading**: Tools can be registered with agents in various ways, including a hot-reloading feature that facilitates rapid development and debugging.
*   **Structured responses**: The `ToolResult` format allows tools to return rich, structured data, including both successful results and detailed error information.

## 11. References

[1] Strands Agents Documentation - Creating Custom Tools: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/custom-tools/index.md
[2] Strands Agents Documentation - Tools Overview: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/index.md
[3] Strands Agents Documentation - @tool Decorator API Reference: https://strandsagents.com/latest/documentation/docs/api-reference/python/tools/decorator/index.md
