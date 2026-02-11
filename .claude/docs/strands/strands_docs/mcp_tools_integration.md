# Strands MCP Tools Integration Report

This report details the integration of Strands Agents with the Model Context Protocol (MCP) for extending agent capabilities with external tools.

## Key Findings

Strands Agents integrate with the Model Context Protocol (MCP) to extend their capabilities through external tools and services. This integration is primarily facilitated by the `strands.tools.mcp.MCPClient` class, which acts as a `ToolProvider`. This allows it to be seamlessly passed into the `Agent` constructor, which then automatically manages the connection lifecycle.

The `MCPClient` is designed to be transport-agnostic, supporting multiple communication protocols for connecting with MCP servers. These include **Standard I/O (stdio)** for local command-line tools, **Streamable HTTP**, and **Server-Sent Events (SSE)** for network-based servers. There are two primary integration patterns. The recommended approach is **Managed Integration**, where the `MCPClient` is passed directly to the `Agent`, and the agent handles the connection lifecycle. For more fine-grained control, **Manual Context Management** can be used, which involves wrapping the MCP client usage within a `with` statement.

Tool discovery is accomplished by calling the `list_tools_sync()` method on an `MCPClient` instance within a managed context. The `MCPClient` also provides several configuration options. The `tool_filters` parameter allows for selective loading of tools using `allowed` and `rejected` lists of strings or regular expressions. To prevent naming collisions when using multiple MCP servers, the `tool_name_prefix` parameter can be used to prepend a prefix to tool names. Furthermore, the `elicitation_callback` parameter enables human-in-the-loop scenarios by allowing tools to request user confirmation before executing critical actions. The primary Python dependencies for this integration are the `strands` and `mcp` packages, with `mcp-proxy-for-aws` being an optional dependency for AWS IAM integration.

## Code Examples

### Quick Start (Python)

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# Create MCP client with stdio transport
mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# Pass MCP client directly to agent - lifecycle managed automatically
agent = Agent(tools=[mcp_client])
agent("What is AWS Lambda?")
```

### Manual Context Management (Python)

```python
with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    agent("What is AWS Lambda?")  # Must be within context
```

### Standard I/O (stdio) Transport (Python)

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

# For macOS/Linux:
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# For Windows:
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=[
            "--from",
            "awslabs.aws-documentation-mcp-server@latest",
            "awslabs.aws-documentation-mcp-server.exe"
        ]
    )
))

with stdio_mcp_client:
    tools = stdio_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    response = agent("What is AWS Lambda?")
```

### Streamable HTTP Transport (Python)

```python
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp import MCPClient

streamable_http_mcp_client = MCPClient(
    lambda: streamablehttp_client("http://localhost:8000/mcp")
)

with streamable_http_mcp_client:
    tools = streamable_http_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
```

### Streamable HTTP with Authentication (Python)

```python
import os
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

github_mcp_client = MCPClient(
    lambda: streamablehttp_client(
        url="https://api.githubcopilot.com/mcp/",
        headers={"Authorization": f"Bearer {os.getenv('MCP_PAT')}"}
    )
)
```

### AWS IAM Integration (Python)

```python
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: aws_iam_streamablehttp_client(
    endpoint="https://your-service.us-east-1.amazonaws.com/mcp",
    aws_region="us-east-1",
    aws_service="bedrock-agentcore"
))
```

### Server-Sent Events (SSE) Transport (Python)

```python
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))

with sse_mcp_client:
    tools = sse_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
```

### Using Multiple MCP Servers (Python)

```python
from mcp import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from strands import Agent
from strands.tools.mcp import MCPClient

# Create multiple clients
sse_mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))
stdio_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="python", args=["path/to/mcp_server.py"])
))

# Manual approach - explicit context management
with sse_mcp_client, stdio_mcp_client:
    tools = sse_mcp_client.list_tools_sync() + stdio_mcp_client.list_tools_sync()
    agent = Agent(tools=tools)

# Managed approach
agent = Agent(tools=[sse_mcp_client, stdio_mcp_client])
```

### Tool Filtering (Python)

```python
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient
import re

# String matching - loads only specified tools
filtered_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )),
    tool_filters={"allowed": ["search_documentation", "read_documentation"]}
)

# Regex patterns
regex_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )),
    tool_filters={"allowed": [re.compile(r"^search_.*")]}
)

# Combined filters - applies allowed first, then rejected
combined_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )),
    tool_filters={
        "allowed": [re.compile(r".*documentation$")],
        "rejected": ["read_documentation"]
    }
)
```

### Tool Name Prefixing (Python)

```python
aws_docs_client = MCPClient(
    lambda: stdio_client(StdioServerParameters(
        command="uvx",
        args=['awslabs.aws-documentation-mcp-server@latest']
    )),
    tool_name_prefix='aws_docs'
)
```

### Elicitation Callback (Python)

```python
# client.py
from mcp import stdio_client, StdioServerParameters
from mcp.types import ElicitResult
from strands import Agent
from strands.tools.mcp import MCPClient

async def elicitation_callback(context, params):
    print(f"ELICITATION: {params.message}")
    # Get user confirmation...
    return ElicitResult(
        action="accept",
        content={"username": "myname"}
    )

client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(command="python", args=["/path/to/server.py"])
    ),
    elicitation_callback=elicitation_callback,
)

with client:
    agent = Agent(tools=client.list_tools_sync())
    result = agent("Delete 'a/b/c.txt' and share the name of the approver")
```

## Classes and Interfaces

The core of the MCP integration is the `strands.tools.mcp.MCPClient` class, which serves as the central point of interaction with MCP servers. It implements the `ToolProvider` interface, making it directly consumable by the `strands.Agent` class. The `MCPClient` relies on various factory functions to establish connections using different transport protocols. For local command-line tools, the `mcp.stdio_client` function is used in conjunction with the `mcp.StdioServerParameters` data class. For network-based communication, `mcp.client.streamable_http.streamablehttp_client` and `mcp.client.sse.sse_client` provide support for Streamable HTTP and Server-Sent Events, respectively. For connecting to MCP servers hosted on AWS with IAM authentication, the `mcp_proxy_for_aws.client.aws_iam_streamablehttp_client` function is available. Finally, the `mcp.types.ElicitResult` data class is used to facilitate human-in-the-loop workflows by representing the user's response during an elicitation process.

## References

[1] [Strands Agents SDK — MCP Tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/index.md)
[2] [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
[3] [Strands Agents SDK — Tool Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/index.md)
