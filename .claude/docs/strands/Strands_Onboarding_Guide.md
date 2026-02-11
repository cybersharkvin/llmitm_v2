# Strands SDK Onboarding Guide: Research & Best Practices

This document serves as the primary onboarding guide for any developer joining the LLMitM v2 project to understand our use of the Strands Agents SDK. It provides a high-level map of the official Strands documentation, followed by a curated set of deep-dive research reports that are essential for understanding our architecture, design patterns, and implementation choices. Each report is summarized to explain its relevance and provide context for why it is required reading.

---

## Strands SDK Documentation Map

This section provides a comprehensive, hierarchically structured map of the Strands Agents SDK documentation, based on the exhaustive research conducted. It is designed to serve as a top-level exploration guide with heavy cross-linking to the official documentation for every feature.

- **[User Guide (Entry Point)](https://strandsagents.com/latest/documentation/docs/user-guide/index.md)**
  - **Core Concepts: Agents**
    - [The Agent Class](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-class/index.md)
    - [The Agent Loop](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-loop/index.md)
    - [Structured Output (with Pydantic)](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/structured-output/index.md)
    - [System Prompts](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/system-prompt/index.md)
    - [Conversation Management](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/conversation-management/index.md)
    - [State Management](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/state/index.md)
  - **Core Concepts: Tools**
    - [Tool Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/index.md)
    - [Custom Tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/custom-tools/index.md)
    - [Tool Executors (`Sequential` vs. `Concurrent`)](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/executors/index.md)
    - [MCP Tools Integration](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/mcp-tools/index.md)
  - **Advanced Concepts**
    - [Hooks System](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/hooks/index.md)
    - [Interrupts (Human-in-the-Loop)](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/interrupts/index.md)
    - [Multi-Agent Patterns (`Graph`, `Swarm`)](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/index.md)
    - [Guardrails & Safety](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/guardrails/index.md)
  - **Model & Session Management**
    - [Model Providers (OpenAI, Bedrock, Ollama)](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/index.md)
    - [Custom Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/custom-model-providers/index.md)
    - [Session Persistence](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/session-persistence/index.md)
  - **Observability & Evaluation**
    - [Observability (OpenTelemetry)](https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/observability/index.md)
    - [Traces](https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/traces/index.md)

---

## Curated Research Reports

### 1. Core Agent Concepts

#### [The Agent Class and Agent Loop](./strands_docs/agent_class_and_agent_loop.md)
This report is the essential starting point for any developer. It provides a deep dive into the `Agent` class, the central component of the Strands SDK, and explains the mechanics of the `AgentLoop`. Understanding this document is critical because our architecture deliberately deviates from the standard loop, using the `Agent` class as a single-shot "compiler" rather than a persistent conversational entity. This report clarifies what Strands provides out-of-the-box and how we have chosen to use it.

#### [Structured Output with Pydantic](./strands_docs/structured_output_with_pydantic.md)
This document explains what is arguably the most critical feature of Strands for our project: structured output. It details how the `structured_output_model` parameter allows us to constrain the LLM's output to a Pydantic schema, ensuring we get back validated, typed data objects (`ActionGraph`, `CriticFeedback`). This is the bridge that makes the LLM's reasoning programmatically useful and is the foundation of our Actor/Critic compilation process.

#### [Prompts and Conversation Management](./strands_docs/prompts_and_conversation_management.md)
This report covers how Strands handles system prompts and manages conversational history. It is important because it justifies our decision to use the `NullConversationManager`. By understanding the default behaviors (like the `SlidingWindowConversationManager`), a developer will appreciate why we explicitly manage context for each LLM call to maintain a stateless, deterministic system.

#### [State Management and Session Persistence](./strands_docs/state_management_and_session_persistence.md)
This document details Strands' built-in mechanisms for managing state (`AgentState`) and persisting sessions (`FileSessionManager`, `RedisSessionManager`). This research is crucial because it validates our architectural decision to *not* use these features. Our single source of truth is the Neo4j graph, and this report clarifies why Strands' session management is redundant in our graph-native architecture.

### 2. Tools & Extensibility

#### [Custom Tools System](./strands_docs/custom_tools_system.md)
This report explains how to define and use custom tools within the Strands SDK using the `@tool` decorator. It is essential reading for understanding how we expose graph-querying capabilities to the LLM during the compilation and repair phases. The document covers tool signatures, context injection, and how tools are provided to the agent.

#### [Tool Executors](./strands_docs/tool_executors.md)
This document details the difference between the `SequentialToolExecutor` and the `ConcurrentToolExecutor`. It is a short but critical report that justifies our use of the `SequentialToolExecutor`. A developer must understand this to avoid breaking the dependency chain in our compilation process, where the LLM may need to call one tool and use its output in a subsequent tool call.

#### [MCP Tools Integration](./strands_docs/mcp_tools_integration.md)
This report covers the integration with the Model Context Protocol (MCP), which allows a Strands agent to communicate with external tools like the Neo4j MCP Server. While not used in our production runtime, this is an important document for developers to understand how they can use MCP for interactive debugging and conversational exploration of the graph during development.

#### [Model Providers and Custom Providers](./strands_docs/model_providers_and_custom_providers.md)
This document explains how Strands abstracts away different LLM backends (OpenAI, Bedrock, Ollama) through a unified `Model` interface. It also covers how to create custom model providers. This is important for understanding how to configure the LLM backend for our Actor and Critic agents and how we could integrate a proprietary model in the future.

### 3. Advanced Concepts

#### [Hooks System](./strands_docs/hooks_system.md)
This report provides a deep dive into the event-driven Hooks system, which allows for callbacks at various points in the agent lifecycle. This is a key document for understanding how we implement cross-cutting concerns. Specifically, it explains the `BeforeToolCallEvent` that we use to implement our human-in-the-loop approval interrupt for destructive actions.

#### [Interrupts and Observability](./strands_docs/interrupts_and_observability.md)
This document covers two advanced but critical features. The Interrupts section details the `tool_context.interrupt()` function, which is the core mechanism for our approval workflow. The Observability section explains how to integrate with OpenTelemetry for tracing and logging, which is essential for debugging and monitoring our agent in a production environment.

#### [Multi-Agent Patterns](./strands_docs/multi_agent_patterns.md)
This report explores Strands' built-in multi-agent capabilities, such as the `Graph` and `Swarm` classes. While our current architecture uses a single custom logic orchestrator, this research is important for our future roadmap. It provides the foundation for how we might decompose our agent into more specialized, collaborative sub-agents.

#### [Guardrails and Safety](./strands_docs/guardrails_and_safety.md)
This document details the safety features within Strands, including built-in guardrails and integration with external safety providers like Amazon Bedrock Guardrails. It is essential reading for understanding how we enforce the "Guarded LLM" principle. This report informs our strategy for preventing prompt injection, mitigating harmful content, and ensuring the agent's actions align with our defined safety policies.
