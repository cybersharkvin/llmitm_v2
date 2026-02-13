# How to Implement Tool Use

> Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use

Step-by-step guide for implementing tools with Claude, including the tool runner, parallel tools, and error handling.

---

## Model Selection

- **Claude Opus 4.6**: Best for complex tools and ambiguous queries. Handles multiple tools well, seeks clarification when needed.
- **Claude Haiku**: Good for straightforward tools. May infer missing parameters.

## Tool Definition

Each tool requires:

| Parameter | Description |
|-----------|-------------|
| `name` | Must match `^[a-zA-Z0-9_-]{1,64}$` |
| `description` | Detailed plaintext: what it does, when to use, parameter meanings, caveats |
| `input_schema` | JSON Schema object defining expected parameters |
| `input_examples` | (Optional, beta) Example input objects |

**Best practice**: Aim for 3-4+ sentences per tool description. More context = better tool selection.

## Tool Runner (Beta)

The SDK provides an out-of-the-box tool execution loop. Available in Python, TypeScript, and Ruby SDKs.

### Python Example

```python
import anthropic
import json
from anthropic import beta_tool

client = anthropic.Anthropic()

@beta_tool
def get_weather(location: str, unit: str = "fahrenheit") -> str:
    """Get the current weather in a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA
        unit: Temperature unit, either 'celsius' or 'fahrenheit'
    """
    return json.dumps({"temperature": "20C", "condition": "Sunny"})

# Auto-loops until Claude is done with tools
runner = client.beta.messages.tool_runner(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
)

# Get final message directly
final_message = runner.until_done()
print(final_message.content[0].text)
```

The `@beta_tool` decorator inspects function arguments and docstring to extract JSON schema.

### Streaming with Tool Runner

```python
runner = client.beta.messages.tool_runner(
    model="claude-opus-4-6",
    max_tokens=1024,
    tools=[get_weather],
    messages=[{"role": "user", "content": "Weather in Paris?"}],
    stream=True,
)

for message_stream in runner:
    for event in message_stream:
        print("event:", event)
```

## Manual Implementation

### Controlling Tool Use with `tool_choice`

| Value | Behavior |
|-------|----------|
| `auto` | Claude decides (default when tools provided) |
| `any` | Must use one of the provided tools |
| `tool` | Must use a specific named tool |
| `none` | No tools (default when no tools provided) |

With `any` or `tool`, Claude will not emit natural language before `tool_use` blocks.

**Note**: `any` and `tool` are NOT compatible with extended thinking. Only `auto` and `none` work with thinking.

### Handling Tool Results

When Claude returns `stop_reason: "tool_use"`:

1. Extract `name`, `id`, `input` from `tool_use` block
2. Execute the tool
3. Return result in a `tool_result` block:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
      "content": "15 degrees"
    }
  ]
}
```

**Critical formatting rules:**
- `tool_result` blocks MUST come FIRST in the content array (before any text)
- Tool result messages must immediately follow the assistant's tool use message

### Error Handling

Return errors with `is_error: true`:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_01A09q90qw90lq917835lq9",
  "content": "ConnectionError: service unavailable (HTTP 500)",
  "is_error": true
}
```

Claude will retry 2-3 times with corrections on invalid tool calls. Use `strict: true` to eliminate invalid calls entirely.

### Parallel Tool Use

Claude may call multiple tools in one response. All results must be in a **single** user message:

```python
# Correct: all results in one message
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "toolu_01", "content": "result1"},
    {"type": "tool_result", "tool_use_id": "toolu_02", "content": "result2"},
]}
```

Disable with `disable_parallel_tool_use=true`.

### Maximizing Parallel Tool Use

Add to system prompt:
```
For maximum efficiency, whenever you need to perform multiple independent operations,
invoke all relevant tools simultaneously rather than sequentially.
```

### Handling `max_tokens` Truncation

If `stop_reason == "max_tokens"` and last block is `tool_use`, retry with higher `max_tokens`.

## JSON Output Mode (Without Tools)

Tools can be used to get structured JSON output without actual tool execution. Define a "tool" with the schema you want, force it with `tool_choice`, and parse the `input` field.
