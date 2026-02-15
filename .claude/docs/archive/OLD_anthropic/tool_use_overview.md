# Tool Use with Claude — Overview

> Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview

How Claude interacts with external tools and functions via the Messages API.

---

## How Tool Use Works

Claude supports two types of tools:

1. **Client tools**: Execute on your systems (user-defined custom tools + Anthropic-defined tools like computer use)
2. **Server tools**: Execute on Anthropic's servers (web search, web fetch) — no implementation required

### Client Tool Flow

1. **Define tools** with names, descriptions, and input schemas in your API request
2. **Claude decides** to use a tool and constructs a formatted request (`stop_reason: "tool_use"`)
3. **You execute** the tool and return results in a `tool_result` content block
4. **Claude uses** the tool result to formulate its final response

### Server Tool Flow

1. **Specify server tools** in API request
2. **Claude executes** the tool internally (server-side sampling loop, up to 10 iterations)
3. **Results incorporated** directly into Claude's response

## Basic Example

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=[
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    }
                },
                "required": ["location"],
            },
        }
    ],
    messages=[{"role": "user", "content": "What's the weather like in San Francisco?"}],
)
```

Response with tool use:

```json
{
  "stop_reason": "tool_use",
  "content": [
    {"type": "text", "text": "I'll check the current weather in San Francisco for you."},
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "get_weather",
      "input": {"location": "San Francisco, CA", "unit": "celsius"}
    }
  ]
}
```

Return tool result:

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=[...],
    messages=[
        {"role": "user", "content": "What's the weather like in San Francisco?"},
        {"role": "assistant", "content": [
            {"type": "text", "text": "I'll check the current weather."},
            {"type": "tool_use", "id": "toolu_01A09q90qw90lq917835lq9",
             "name": "get_weather", "input": {"location": "San Francisco, CA"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
             "content": "65 degrees"},
        ]},
    ],
)
```

## Key Patterns

### Sequential Tools

Claude calls tools one at a time when outputs are dependent. Example: `get_location` → `get_weather`.

### Parallel Tools

Claude can call multiple independent tools in a single response. All `tool_use` blocks appear in one assistant message; all `tool_result` blocks must be in the subsequent user message.

### Missing Information

Claude Opus asks for missing required parameters. Claude Sonnet/Haiku may infer values.

## MCP Tool Integration

Convert MCP tools to Claude format by renaming `inputSchema` to `input_schema`:

```python
async def get_claude_tools(mcp_session):
    mcp_tools = await mcp_session.list_tools()
    return [
        {
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        }
        for tool in mcp_tools.tools
    ]
```

## Pricing

Tool use is priced on input + output tokens. Additional tokens come from:
- The `tools` parameter (names, descriptions, schemas)
- `tool_use` and `tool_result` content blocks
- Auto-injected system prompt (~346 tokens for Claude 4.x with `auto`/`none` tool choice)

## `pause_turn` Stop Reason

Server-side sampling loop has a 10-iteration default limit. If reached, API returns `stop_reason="pause_turn"`. Continue by sending the response back to let Claude finish.
