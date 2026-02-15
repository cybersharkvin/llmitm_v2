# Programmatic Tool Calling

> Source: https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling

Claude writes code that calls tools programmatically within a code execution container, reducing latency and token consumption for multi-tool workflows.

---

**Status**: Public beta. Requires `"advanced-tool-use-2025-11-20"` beta header and code execution tool.

**Available on**: Claude Opus 4.6, Claude Sonnet 4.5, Claude Opus 4.5.

## Overview

Instead of separate API round-trips for each tool call, Claude writes Python code that invokes tools as functions. The code runs in a sandboxed container, pausing when a tool function is called. You provide the result, and execution continues.

**Benefits:**
- Tool results from programmatic calls are NOT added to Claude's context (only final code output is)
- Multiple tool calls in one code execution = fewer model round-trips
- Claude can filter/aggregate data before it reaches the context window
- Conditional logic and early termination without extra API calls

## Core Concept: `allowed_callers`

```json
{
  "name": "query_database",
  "description": "Execute a SQL query",
  "input_schema": {...},
  "allowed_callers": ["code_execution_20250825"]
}
```

Values:
- `["direct"]` — Only Claude calls directly (default)
- `["code_execution_20250825"]` — Only callable from code execution
- `["direct", "code_execution_20250825"]` — Both (not recommended)

## Example

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    betas=["advanced-tool-use-2025-11-20"],
    max_tokens=4096,
    messages=[{"role": "user", "content": "Query sales for West, East, Central regions"}],
    tools=[
        {"type": "code_execution_20250825", "name": "code_execution"},
        {
            "name": "query_database",
            "description": "Execute SQL. Returns list of JSON rows.",
            "input_schema": {
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
            "allowed_callers": ["code_execution_20250825"],
        },
    ],
)
```

Claude writes code like:
```python
results = await query_database("SELECT region, SUM(revenue) FROM sales GROUP BY region")
top = max(results, key=lambda x: x["revenue"])
print(f"Top region: {top['region']} with ${top['revenue']:,}")
```

## Advanced Patterns

- **Batch processing with loops**: N regions in 1 execution instead of N round-trips
- **Early termination**: `break` when success criteria met
- **Conditional tool selection**: Choose tool based on intermediate results
- **Data filtering**: Filter large results before returning to Claude

## Constraints

- Tools with `strict: true` NOT supported with programmatic calling
- `tool_choice` cannot force programmatic calling
- `disable_parallel_tool_use` not supported
- Web search, web fetch, MCP tools cannot be called programmatically (yet)
- Tool result responses must contain ONLY `tool_result` blocks (no text)

## Token Efficiency

Tool results from programmatic invocations do NOT count toward input/output token usage. Only final code execution result and Claude's response count. Calling 10 tools programmatically uses ~1/10th the tokens of 10 direct calls.
