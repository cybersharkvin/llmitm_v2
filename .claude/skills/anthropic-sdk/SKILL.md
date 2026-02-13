---
name: anthropic-sdk
description: Anthropic Python SDK documentation — messages API, structured output, programmatic tool calling, code execution sandbox, beta features, and prompt engineering. Use when writing or modifying agent code, implementing tool use, or working with the Anthropic API.
allowed-tools: Read, Grep, Glob
---

# Anthropic Documentation Reference for LLMitM v2

This is the top-level guide to Anthropic's documentation as it applies to this project. It is written for anyone working on LLMitM v2 — whether you're the original author returning after a break or a new contributor getting up to speed.

LLMitM v2 uses the Anthropic Python SDK to power two agents: a **Recon Agent** (ProgrammaticAgent) that explores targets inside a code execution sandbox, and an **Attack Critic** (SimpleAgent) that adversarially validates plans. The LLM's job is to *compile* deterministic ActionGraphs — it runs once, then the graph executes forever without LLM involvement. Everything below is organized around that reality.

---

## Quick Reference: Documentation Directories

| Directory | Index | Summary |
|-----------|-------|---------|
| **[Developer Guide](../../docs/anthropic/developer_guide/CLAUDE.md)** | 110 docs | API usage patterns, tool calling, prompt engineering, structured outputs, and SDK features. **Use when** writing or modifying agent code, designing prompts, implementing tool use, or optimizing cost/latency. **Don't use** for REST endpoint signatures, admin/org management, or billing — that's API Reference territory. |
| **[API Reference](../../docs/anthropic/api_reference/CLAUDE.md)** | 122 docs | REST endpoints, SDK installation, request/response schemas, error codes, rate limits, and org admin. **Use when** you need exact endpoint parameters, error handling details, SDK setup, or rate limit math. **Don't use** for understanding *how* to design prompts or *why* to choose a pattern — that's Developer Guide territory. |
| **[Resources](../../docs/anthropic/resources/CLAUDE.md)** | 76 docs | Prompt templates and use-case examples organized by domain (code, data extraction, security, creative). **Use when** you need inspiration for prompt structure or want to see how Anthropic recommends framing a specific task type. **Don't use** as authoritative API docs — these are examples, not specifications. |

---

## How We Use the Anthropic API

Our entire LLM integration lives in `llmitm_v2/orchestrator/agents.py`. Two classes, two API patterns:

| Agent | Class | API Call | Purpose |
|-------|-------|----------|---------|
| **Recon Agent** | `ProgrammaticAgent` | `client.beta.messages.create()` | Writes Python in a sandbox, calls `await mitmdump(...)`, produces ActionGraphs |
| **Attack Critic** | `SimpleAgent` | `client.messages.parse()` | Single-shot structured output, validates ActionGraphs via `CriticFeedback` |

Both patterns enforce Pydantic schemas on the output. The Recon Agent uses programmatic tool calling (code execution + custom tools). The Critic uses grammar-constrained decoding (structured output). Understanding *both* patterns is essential.

---

## Critical Documentation (Read These First)

These are the docs you must internalize before touching the agent code. Each one maps directly to a pattern we use.

### 1. Programmatic Tool Calling
**File**: [developer_guide/programmatic_tool_calling.md](../../docs/anthropic/developer_guide/programmatic_tool_calling.md)

This is the most important doc for understanding the Recon Agent. It explains how Claude writes Python code that calls custom tools via `await tool(...)` inside a sandboxed container, with intermediate results staying in the sandbox (not entering the context window).

**How we use it**:
- `ProgrammaticAgent.__call__()` manually implements the tool-result loop described in Steps 1-5 of this doc
- Our `handle_mitmdump` tool uses `allowed_callers: ["code_execution_20250825"]` so it's only callable from the sandbox
- We preserve `container_id` across turns for sandbox continuity (a hard-won bug fix — see activeContext.json)
- Tool results from programmatic calls don't count toward token usage — this is why we chose this pattern over direct tool calling

**Key gotchas we've hit**:
- `block.input` is a raw string (not dict) for programmatic calls — `_sanitize_content()` handles this
- `output_format` is incompatible with programmatic tool calling — use `create()` not `parse()` when tools are present
- Only Opus 4.6, Sonnet 4.5, and Opus 4.5 support programmatic tool calling (NOT Haiku)

### 2. Code Execution Tool
**File**: [developer_guide/code_execution_tool.md](../../docs/anthropic/developer_guide/code_execution_tool.md)

The sandbox that powers programmatic tool calling. The Recon Agent runs inside this.

**How we use it**:
- Beta header: `code-execution-2025-08-25`
- Tool type: `code_execution_20250825`
- Container has no internet access — all external calls go through our `mitmdump` custom tool
- Container expires after ~4.5 minutes of inactivity — we must respond to tool calls before expiry
- `code_execution_tool_result.stdout` can be 300K+ chars — `_truncate_dict()` recursively caps oversized blocks

### 3. Structured Outputs
**File**: [developer_guide/structured_outputs.md](../../docs/anthropic/developer_guide/structured_outputs.md)

Grammar-constrained decoding guarantees valid JSON matching a Pydantic schema. This is how the Attack Critic works.

**How we use it**:
- `client.messages.parse(output_format=CriticFeedback)` — returns `response.parsed_output` as a validated Pydantic instance
- `client.messages.parse(output_format=ActionGraph)` — used when the Recon Agent needs structured output without tools
- `output_format` is deprecated in favor of `output_config.format` — we should migrate (deferred tech debt)
- Grammar compilation has ~1-2s first-call latency, then cached 24h server-side

**Key gotchas**:
- `strict: true` tools are NOT compatible with programmatic tool calling
- Structured outputs + tool use can coexist, but not structured outputs + programmatic tool calling
- If `stop_reason == "max_tokens"`, the output may not match the schema — bump `max_tokens`

### 4. How to Implement Tool Use
**File**: [developer_guide/how_to_implement_tool_use.md](../../docs/anthropic/developer_guide/how_to_implement_tool_use.md)

The comprehensive tool use guide. Covers tool definitions, the tool call loop, parallel tool use, error handling, and the `tool_runner` beta.

**How we use it**:
- Tool schemas follow the `name` / `description` / `input_schema` pattern from this doc
- We do NOT use the `tool_runner` — we implement the loop manually in `ProgrammaticAgent.__call__()` for control over container_id, truncation, and budget enforcement
- Tool result formatting is strict: `tool_result` blocks must come FIRST in the user message content array, no text before them
- Detailed tool descriptions are critical — our `MITMDUMP_TOOL_SCHEMA` follows the "good description" pattern from this doc

### 5. Beta Headers
**File**: [api_reference/beta_headers.md](../../docs/anthropic/api_reference/beta_headers.md)

We use two beta headers simultaneously:
- `code-execution-2025-08-25` — enables the code execution sandbox
- `advanced-tool-use-2025-11-20` — enables programmatic tool calling (allowed_callers)

Both are passed via `betas=[...]` on `client.beta.messages.create()`. Multiple betas are comma-separated in raw HTTP but list-form in the SDK.

### 6. Python SDK
**File**: [api_reference/python_sdk.md](../../docs/anthropic/api_reference/python_sdk.md)

We use `anthropic` v0.79.0+. Key SDK features:
- `client.messages.parse()` — structured output with Pydantic model, returns `.parsed_output`
- `client.beta.messages.create()` — beta namespace for code execution + programmatic tools
- `response.usage` — token tracking (input_tokens, output_tokens) logged after every call
- Sync client only (no async) — design decision to avoid complexity

---

## Important Secondary Documentation

These docs are relevant but not as immediately critical. Read them when you need to go deeper on a specific topic.

### Prompt Engineering & System Prompts
- [developer_guide/give_claude_a_role_system_prompts.md](../../docs/anthropic/developer_guide/give_claude_a_role_system_prompts_giving_claude_a_role_with_a_system_prompt.md) — Our `RECON_SYSTEM_PROMPT` and `CRITIC_SYSTEM_PROMPT` are the most impactful levers for agent quality. System prompt design matters more than model choice.
- [developer_guide/use_xml_tags.md](../../docs/anthropic/developer_guide/use_xml_tags_use_xml_tags_to_structure_your_prompts.md) — We use XML tags in skill guides and system prompts to separate context sections.
- [developer_guide/chain_complex_prompts.md](../../docs/anthropic/developer_guide/chain_complex_prompts_chain_complex_prompts_for_stronger_performance.md) — The Actor/Critic loop is essentially prompt chaining: Recon Agent produces → Critic validates → loop.
- [developer_guide/let_claude_think_cot.md](../../docs/anthropic/developer_guide/let_claude_think_cot_let_claude_think_chain_of_thought_prompting_to_increase_performance.md) — Relevant for improving Recon Agent reasoning quality.

### Cost & Performance
- [developer_guide/pricing.md](../../docs/anthropic/developer_guide/pricing.md) — Sonnet 4.5 costs ~$3/M input, $15/M output. Our token budget (50-150K) keeps runs under $1.
- [developer_guide/reducing_latency.md](../../docs/anthropic/developer_guide/reducing_latency.md) — Programmatic tool calling reduces latency vs. direct tool use by eliminating model round-trips.
- [api_reference/rate_limits.md](../../docs/anthropic/api_reference/rate_limits.md) — Each programmatic tool call counts as a separate invocation against rate limits.
- [developer_guide/prompt_caching.md](../../docs/anthropic/developer_guide/prompt_caching.md) — Could cache our system prompts + skill guides (not yet implemented).

### Models & Capabilities
- [developer_guide/models_overview.md](../../docs/anthropic/developer_guide/models_overview.md) — Model capabilities matrix. Programmatic tool calling: Opus 4.6, Sonnet 4.5, Opus 4.5 only.
- [developer_guide/choosing_a_model.md](../../docs/anthropic/developer_guide/choosing_a_model_choosing_the_right_model.md) — We use Sonnet 4.5 for the Recon Agent (best cost/capability ratio for tool use) and could use Haiku for the Critic (simpler task, but currently same model).
- [developer_guide/whats_new_in_claude_46.md](../../docs/anthropic/developer_guide/whats_new_in_claude_46.md) — Opus 4.6 features. Relevant if we upgrade the Recon Agent for harder targets.

### Quality & Safety
- [developer_guide/reduce_hallucinations.md](../../docs/anthropic/developer_guide/reduce_hallucinations.md) — The Recon Agent hallucinates credentials (known issue). Techniques here could help.
- [developer_guide/mitigate_jailbreaks.md](../../docs/anthropic/developer_guide/mitigate_jailbreaks_mitigate_jailbreaks_and_prompt_injections.md) — Defense patterns. Our agents process untrusted HTTP traffic — prompt injection via response headers is a real risk.

### Tool Use Extensions
- [developer_guide/overview_tool_use_with_claude.md](../../docs/anthropic/developer_guide/overview_tool_use_with_claude.md) — High-level tool use concepts. Read first if you're new to Claude tool use entirely.
- [developer_guide/custom_tools.md](../../docs/anthropic/developer_guide/custom_tools.md) — Agent SDK custom tools. We don't use the Agent SDK but the patterns are similar.
- [developer_guide/fine_grained_tool_streaming.md](../../docs/anthropic/developer_guide/fine_grained_tool_streaming.md) — Not currently used but relevant if we add streaming to the agent pipeline.

---

## Documentation We Don't Use (and Why)

These sections exist in the subdirectories but are not relevant to LLMitM v2's architecture:

- **Agent SDK** (developer_guide) — We use the raw Anthropic API, not the Agent SDK. Our orchestrator owns all control flow.
- **MCP / Remote MCP** — We don't use Model Context Protocol. Our tools are host-side Python functions.
- **Agent Skills API** — Anthropic's managed skill system. Our skills are local markdown files loaded into the system prompt.
- **Computer Use / Web Search / Web Fetch tools** — Server-managed tools we don't need. Our agent uses code_execution + custom mitmdump tool only.
- **Extended Thinking / Adaptive Thinking** — Not used. Our agents are single-shot or few-shot; extended thinking adds latency without benefit for our use case.
- **Vision / PDF / Multimodal** — We work with HTTP traffic text, not images or documents.
- **Batch Processing** — We make individual API calls in a loop, not batch requests.
- **All C# / TypeScript / Java / Go / Ruby / PHP SDK docs** — We use Python exclusively.
- **Admin / Organization / Workspace management** — Irrelevant to the application code.
- **Resources directory creative prompts** — Prompt templates for creative writing, games, etc. Not applicable.

---

## Subdirectory Indexes

Each subdirectory has its own categorized CLAUDE.md with full file listings:

- **[Developer Guide](../../docs/anthropic/developer_guide/CLAUDE.md)** — 110 docs covering API usage, Agent SDK, tools, prompt engineering, structured outputs, performance, platform integrations, and enterprise features. Organized into 16 categories.
- **[API Reference](../../docs/anthropic/api_reference/CLAUDE.md)** — 122 docs covering REST endpoints, SDKs, admin APIs, and billing. Organized into 10 categories with a quick-reference section.
- **[Resources](../../docs/anthropic/resources/CLAUDE.md)** — 76 docs containing prompt templates and use case guides. Organized into 12 categories with relevance markers (HIGH/MODERATE/LOW).

---

## Quick Reference: Our API Call Patterns

### Pattern 1: Structured Output (Attack Critic)
```python
# SimpleAgent.__call__() — single API call, grammar-constrained
response = client.messages.parse(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    system=CRITIC_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": prompt}],
    output_format=CriticFeedback,  # Pydantic model → grammar-constrained JSON
)
result = response.parsed_output  # CriticFeedback instance, guaranteed valid
```

### Pattern 2: Programmatic Tool Calling (Recon Agent)
```python
# ProgrammaticAgent.__call__() — multi-turn loop with code execution
response = client.beta.messages.create(
    model="claude-sonnet-4-5-20250929",
    betas=["code-execution-2025-08-25", "advanced-tool-use-2025-11-20"],
    max_tokens=16384,
    system=RECON_SYSTEM_PROMPT,
    messages=messages,
    container=container_id,  # Preserve sandbox state across turns
    tools=[
        {"type": "code_execution_20250825", "name": "code_execution"},
        {
            "name": "mitmdump",
            "description": "Run mitmdump command...",
            "input_schema": {"type": "object", "properties": {"command": {...}}},
            "allowed_callers": ["code_execution_20250825"],  # Only from sandbox
        },
    ],
)
# Then loop: check stop_reason, dispatch tool calls, send results back
```

### Pattern 3: Actor/Critic Loop (Orchestrator._compile)
```python
for iteration in range(MAX_CRITIC_ITERATIONS):
    # Actor: Recon Agent produces ActionGraph
    agent_result = recon_agent(context, structured_output_model=ActionGraph)
    action_graph = agent_result.structured_output

    # Critic: Attack Critic validates
    critic_result = attack_critic(
        action_graph.model_dump_json(),
        structured_output_model=CriticFeedback,
    )
    if critic_result.structured_output.passed:
        break  # ActionGraph accepted
    # Otherwise: append feedback to context, retry
```

---

## Known SDK Bugs & Workarounds

These are issues we've encountered with `anthropic` SDK v0.79.0 that are documented in `activeContext.json`:

1. **`model_dump()` serializes `tool_use.input` as string** — `_sanitize_content()` manually rebuilds the dict for programmatic tool_use blocks
2. **`beta.messages.create()` rejects `output_format` with Pydantic model** — use `parse()` for structured output, `create()` for tool use; never both
3. **`container_id` not automatically preserved** — must extract from `response.container.id` and pass back on next call
4. **`code_execution_tool_result.stdout` can exceed 300K chars** — `_truncate_dict()` recursively caps blocks to prevent context explosion
5. **`output_format` is deprecated** — should migrate to `output_config.format` (deferred)
