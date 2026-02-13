# Anthropic API Documentation Index

Local copies of Anthropic's official documentation, curated for the LLMitM v2 project. These docs are the authoritative reference for our migration from Strands SDK to Anthropic's native API.

---

## Why These Docs Exist

We discovered that Strands SDK implements structured output as a **fake tool call** (`tool_choice: {"any": {}}`) rather than using Anthropic's native grammar-constrained decoding. This caused ~1300 API calls and $46 in credits for what should have been ~16 invocations. These docs capture the correct way to use Anthropic's API directly.

---

## Core Documents

### [Structured Outputs](./structured_outputs.md)

**This is the most critical document for our migration.** It explains Anthropic's native structured output via `output_config.format` — grammar-constrained decoding that guarantees schema compliance at the token-generation level with zero extra API calls. This is what Strands should have been using but isn't. Our Pydantic models (`ActionGraph`, `CriticFeedback`, `ReconReport`, `RepairDiagnosis`) map directly to the `json_schema` format type. The Python SDK's `client.messages.parse()` with Pydantic models is our primary integration path.

### [Tool Use Overview](./tool_use_overview.md)

Explains the Messages API tool protocol: how Claude decides to use tools, the `tool_use` / `tool_result` message flow, and pricing. Essential for understanding the agent loop we need to implement for the recon agent (which needs real tools like `http_request` and `shell_command`). Key insight: each tool call round-trip is a separate API call — this is protocol-level and unavoidable, but structured output should NOT add extra calls on top.

### [Implement Tool Use](./implement_tool_use.md)

Step-by-step implementation guide including the new **Tool Runner** (beta) which provides an out-of-the-box agent loop. The `@beta_tool` decorator and `client.beta.messages.tool_runner()` may simplify our recon agent implementation. Also covers `tool_choice` control, parallel tool use, error handling, and the critical formatting rules for `tool_result` messages.

### [Programmatic Tool Calling](./programmatic_tool_calling.md)

Advanced pattern where Claude writes code that calls tools within a sandboxed execution container. Dramatically reduces API round-trips for multi-tool workflows. Could be relevant for our recon agent (which makes many HTTP requests), but requires the code execution beta and has constraints (no `strict: true`, no MCP tools). Worth evaluating post-migration.

### [Agent Skills](./agent_skills.md)

Higher-level abstraction for composable agent capabilities via code execution containers. Not directly applicable to our current architecture, but documents Anthropic's direction for agent tooling. Included for completeness and future reference.

---

## Migration Mapping: Strands → Anthropic SDK

| Strands Concept | Anthropic SDK Equivalent |
|-----------------|-------------------------|
| `Agent(model=AnthropicModel(...))` | `anthropic.Anthropic()` client |
| `agent(prompt, structured_output_model=X)` | `client.messages.parse(output_format=X)` |
| `result.structured_output` | `response.parsed_output` |
| `@tool` decorator | `@beta_tool` or raw `input_schema` dict |
| `NullConversationManager` | Default (no conversation management needed) |
| `SequentialToolExecutor` | Manual loop or `tool_runner()` |
| `callback_handler=None` | N/A (no callback system) |

## Key API Parameters

| Parameter | Purpose | Used For |
|-----------|---------|----------|
| `output_config.format` | Native structured output (constrained decoding) | Actor, Critic, Recon, Recon Critic |
| `tools` | Tool definitions with `input_schema` | Recon Agent (http_request, shell_command) |
| `tool_choice` | Control tool selection (`auto`, `any`, `tool`, `none`) | Force/prevent tool use |
| `strict: true` | Guarantee tool input schema compliance | Recon tools |
| `system` | System prompt | Agent personas |
| `max_tokens` | Output length limit | 16384 for Actor, 4096 for Critics |
