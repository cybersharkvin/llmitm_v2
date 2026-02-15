# Structured Outputs

> Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs

Get validated JSON results from agent workflows via grammar-constrained decoding.

---

## Overview

Structured outputs constrain Claude's responses to follow a specific schema, ensuring valid, parseable output for downstream processing. Two complementary features:

- **JSON outputs** (`output_config.format`): Get Claude's response in a specific JSON format
- **Strict tool use** (`strict: true`): Guarantee schema validation on tool names and inputs

These can be used independently or together.

**Available on**: Claude Opus 4.6, Claude Sonnet 4.5, Claude Opus 4.5, and Claude Haiku 4.5 (Claude API and Amazon Bedrock).

## Why Use Structured Outputs

Without structured outputs, Claude can generate malformed JSON or invalid tool inputs. Structured outputs guarantee schema-compliant responses through **constrained decoding**:

- **Always valid**: No more `JSON.parse()` errors
- **Type safe**: Guaranteed field types and required fields
- **Reliable**: No retries needed for schema violations

## JSON Outputs

Control Claude's response format via `output_config.format`.

### Quick Start (Python)

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Extract the key information from this email: John Smith (john@example.com) is interested in our Enterprise plan.",
        }
    ],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "plan_interest": {"type": "string"},
                    "demo_requested": {"type": "boolean"},
                },
                "required": ["name", "email", "plan_interest", "demo_requested"],
                "additionalProperties": False,
            },
        }
    },
)
print(response.content[0].text)
```

**Response**: Valid JSON matching your schema in `response.content[0].text`:

```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "plan_interest": "Enterprise",
  "demo_requested": true
}
```

### Using Pydantic Models (Python SDK)

#### `client.messages.parse()` (Recommended)

Automatically transforms Pydantic model, validates response, returns `parsed_output`:

```python
from pydantic import BaseModel
import anthropic


class ContactInfo(BaseModel):
    name: str
    email: str
    plan_interest: str
    demo_requested: bool


client = anthropic.Anthropic()

response = client.messages.parse(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
    output_format=ContactInfo,
)

contact = response.parsed_output
print(contact.name, contact.email)
```

#### `transform_schema()` Helper

For manual schema transformation before sending:

```python
from anthropic import transform_schema

schema = transform_schema(ContactInfo)

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}],
    output_config={
        "format": {"type": "json_schema", "schema": schema},
    },
)
```

### SDK Schema Transformation

The Python SDK automatically:

1. Removes unsupported constraints (e.g., `minimum`, `maximum`, `minLength`)
2. Updates descriptions with constraint info (e.g., "Must be at least 100")
3. Adds `additionalProperties: false` to all objects
4. Filters string formats to supported list only
5. Validates responses against your original schema (with all constraints)

## Strict Tool Use

Validates tool parameters with `strict: true`, ensuring Claude calls functions with correctly-typed arguments.

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What's the weather like in San Francisco?"}],
    tools=[
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                    },
                },
                "required": ["location"],
                "additionalProperties": False,
            },
        }
    ],
)
```

**Guarantees:**
- Tool `input` strictly follows the `input_schema`
- Tool `name` is always valid

## Using Both Together

JSON outputs + strict tool use in the same request:

```python
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Help me plan a trip to Paris for next month"}
    ],
    # JSON outputs: structured response format
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "next_steps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["summary", "next_steps"],
                "additionalProperties": False,
            },
        }
    },
    # Strict tool use: guaranteed tool parameters
    tools=[
        {
            "name": "search_flights",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "date": {"type": "string", "format": "date"},
                },
                "required": ["destination", "date"],
                "additionalProperties": False,
            },
        }
    ],
)
```

## Performance Considerations

### Grammar Compilation and Caching

- **First request latency**: Additional latency while grammar is compiled
- **Automatic caching**: Compiled grammars cached for 24 hours
- **Cache invalidation**: Changing JSON schema structure or tool set invalidates cache. Changing only `name`/`description` does NOT.

### Token Costs

- Claude receives an additional system prompt explaining expected output format
- Input token count will be slightly higher
- Changing `output_config.format` invalidates prompt cache

## JSON Schema Limitations

### Supported

- All basic types: object, array, string, integer, number, boolean, null
- `enum` (strings, numbers, bools, or nulls only)
- `const`, `anyOf`, `allOf` (with limitations)
- `$ref`, `$def`, `definitions` (no external `$ref`)
- `default`, `required`, `additionalProperties` (must be `false` for objects)
- String formats: `date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid`
- Array `minItems` (only 0 and 1)

### Not Supported

- Recursive schemas
- Complex types within enums
- External `$ref`
- Numerical constraints (`minimum`, `maximum`, `multipleOf`)
- String constraints (`minLength`, `maxLength`)
- Array constraints beyond `minItems` of 0 or 1
- `additionalProperties` set to anything other than `false`

### Pattern Support (Regex)

**Supported**: Full matching, quantifiers (`*`, `+`, `?`, `{n,m}`), character classes, groups.

**Not supported**: Backreferences, lookahead/lookbehind, word boundaries, complex `{n,m}` with large ranges.

## Invalid Outputs

### Refusals (`stop_reason: "refusal"`)

Claude maintains safety properties. On refusal: `stop_reason: "refusal"`, output may not match schema.

### Token Limit (`stop_reason: "max_tokens"`)

If cut off: incomplete output, retry with higher `max_tokens`.

## Feature Compatibility

**Works with**: Batch processing, token counting, streaming, combined JSON outputs + strict tools.

**Incompatible with**: Citations, message prefilling (for JSON outputs).

**Grammar scope**: Grammars apply only to Claude's direct output, not to tool use calls, tool results, or thinking tags.

## Migration Note

`output_format` has moved to `output_config.format`. The old parameter still works temporarily but is deprecated. Beta headers are no longer required.
