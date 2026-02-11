# Technical Research Report: Strands Prompts and Conversation Management

This report provides a comprehensive overview of prompts and conversation management within the Strands Agents SDK for Python, based on the official documentation.

## 1. Prompts

In the Strands Agents SDK, prompts are the primary means of interaction with AI models. This includes both system-level instructions and user-initiated messages.

### 1.1. System Prompts

System prompts are used to provide high-level instructions to the model, defining its role, capabilities, and constraints. These prompts establish the foundational behavior of the agent throughout a conversation. The system prompt is specified during the instantiation of an `Agent` object.

If a system prompt is not provided, the agent will operate based on the model's default settings.

### 1.2. User Messages

User messages represent the queries and requests made to the agent. The SDK supports several methods for sending these messages.

#### 1.2.1. Text Prompts

The most direct way to interact with an agent is through a simple text prompt.

#### 1.2.2. Multi-Modal Prompts

The SDK supports multi-modal content, allowing for the inclusion of images, documents, and other non-textual elements in user messages.

#### 1.2.3. Direct Tool Calls

The SDK provides a mechanism to bypass the natural language interface and execute tools directly. By default, these tool calls are recorded in the conversation history. This behavior can be overridden by setting `record_direct_tool_call=False`.

## 2. Conversation Management

As a conversation progresses, managing the context becomes increasingly important. The Strands Agents SDK provides a flexible `ConversationManager` interface to implement various strategies for managing the conversation history.

### 2.1. NullConversationManager

The `NullConversationManager` is a basic implementation that does not alter the conversation history. It is suitable for short conversations, debugging, or scenarios where context is managed manually.

### 2.2. SlidingWindowConversationManager

The `SlidingWindowConversationManager` is the default conversation manager in the SDK. It employs a sliding window strategy, maintaining a fixed number of the most recent messages. The size of this window is determined by the `window_size` parameter.

This manager also supports per-turn context management through the `per_turn` parameter. When set to `True`, management is applied before each model call. If set to an integer `N`, it is applied every `N` model calls.

### 2.3. SummarizingConversationManager

The `SummarizingConversationManager` utilizes intelligent summarization to manage the conversation context. Instead of discarding older messages, it summarizes them, preserving key information while adhering to token limits.

This manager offers several customization options, including `summary_ratio` (the percentage of messages to summarize), `preserve_recent_messages` (the number of recent messages to keep), and the ability to use a custom `summarization_agent` or `summarization_system_prompt` for domain-specific summarization.

### 2.4. Custom ConversationManager

For more advanced use cases, a custom conversation manager can be created by implementing the `ConversationManager` interface. This requires defining the `apply_management` and `reduce_context` methods to implement a custom context management strategy.

## References

[1] [Strands Agents SDK — System Prompts](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/system-prompt/index.md)
[2] [Strands Agents SDK — Conversation Management](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/conversation-management/index.md)
[3] [Strands Agents SDK — Agent Class](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-class/index.md)
