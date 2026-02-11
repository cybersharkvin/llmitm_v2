# Strands Agent Class and Agent Loop: A Technical Deep Dive

This report provides a comprehensive technical overview of the Strands Agent Class and the Agent Loop, based on the official Strands SDK documentation. It covers the core concepts, class structures, and the complete lifecycle of an agent invocation.

## 1. The Agent Loop: Core Concepts

The agent loop is the fundamental orchestration layer in the Strands SDK. It enables a language model to perform complex tasks that require interaction with external systems, such as reading files, querying databases, or calling APIs. The loop manages a cycle of reasoning and action, allowing the model to tackle problems that require multiple steps and external information [1].

### 1.1. How the Loop Works

The agent loop operates on a simple, recursive principle:

1.  **Reasoning (LLM):** The model receives the initial input and the current conversation history (context).
2.  **Tool Selection:** Based on the context, the model decides whether to produce a final response or to use a tool to gather more information or perform an action.
3.  **Tool Execution:** If the model decides to use a tool, the system executes the requested tool with the provided parameters.
4.  **Context Update:** The result of the tool execution (or any error that occurred) is added to the conversation history.
5.  **Repeat:** The loop repeats from step 1, with the updated context.

This cycle continues until the model determines that it has sufficient information to generate a final response to the user's request [1]. The power of this approach lies in the accumulation of context. With each iteration, the model gains a more complete understanding of the task, its previous actions, and the results of those actions.

### 1.2. Messages and Conversation History

The conversation history is the agent's working memory and is composed of a series of messages. There are two primary roles for messages:

*   **User Messages:** These contain the initial user request, any subsequent follow-up instructions, and the results from tool executions.
*   **Assistant Messages:** These represent the model's output, which can include text responses for the user, requests to use a tool, or reasoning traces [1].

### 1.3. Tool Execution

When the model requests the use of a tool, the execution system performs the following steps:

1.  Validates the tool request against the tool's defined schema.
2.  Locates the tool in the tool registry.
3.  Executes the tool with the specified parameters, including error handling.
4.  Formats the result (or any error) as a tool result message and appends it to the conversation history.

This robust error handling allows the model to attempt recovery or try alternative approaches if a tool fails [1].

### 1.4. Agent Loop Lifecycle and Stop Reasons

The agent loop has a well-defined lifecycle with specific entry and exit points. The loop terminates when the model's invocation ends with one of the following stop reasons:

| Stop Reason              | Description                                                                                             | Loop Action  |
| ------------------------ | ------------------------------------------------------------------------------------------------------- | ------------ |
| `end_turn`               | The model has completed its response and has no further actions.                                        | Terminate    |
| `tool_use`               | The model has requested the use of one or more tools.                                                   | Continue     |
| `max_tokens`             | The model's response was truncated because it reached the maximum token limit.                          | Error        |
| `stop_sequence`          | The model encountered a configured stop sequence.                                                       | Terminate    |
| `content_filtered`       | The response was blocked by safety mechanisms.                                                          | Terminate    |
| `guardrail_intervention` | A guardrail policy stopped the generation.                                                              | Terminate    |

[1]

## 2. The `strands.agent.agent.Agent` Class

The `Agent` class is the core implementation of the agent interface in the Strands SDK. It orchestrates the entire workflow of receiving user input, interacting with the language model, executing tools, and producing a final response [2].

### 2.1. `Agent` Constructor

The `Agent` class is initialized with a wide range of parameters to configure its behavior. The constructor signature is as follows:

```python
class Agent(AgentBase):
    def __init__(
        self,
        model: Model | str | None = None,
        messages: Messages | None = None,
        tools: list[Union[str, dict[str, str], "ToolProvider", Any]] | None = None,
        system_prompt: str | list[SystemContentBlock] | None = None,
        structured_output_model: type[BaseModel] | None = None,
        callback_handler: Callable[..., Any] | _DefaultCallbackHandlerSentinel | None = _DEFAULT_CALLBACK_HANDLER,
        conversation_manager: ConversationManager | None = None,
        record_direct_tool_call: bool = True,
        load_tools_from_directory: bool = False,
        trace_attributes: Mapping[str, AttributeValue] | None = None,
        *,
        agent_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        state: AgentState | dict | None = None,
        hooks: list[HookProvider] | None = None,
        session_manager: SessionManager | None = None,
        structured_output_prompt: str | None = None,
        tool_executor: ToolExecutor | None = None,
        retry_strategy: ModelRetryStrategy | _DefaultRetryStrategySentinel | None = _DEFAULT_RETRY_STRATEGY,
    ):
```

[2]

Key parameters include:

*   `model`: The language model to use for inference.
*   `tools`: A list of tools available to the agent.
*   `system_prompt`: A prompt to guide the model's behavior.
*   `conversation_manager`: Manages the conversation history and context window.
*   `max_turns`: The maximum number of turns (iterations) the agent can take before stopping. This is not an explicit parameter in the constructor but is managed through the `invocation_state`.

### 2.2. Invoking the Agent: `__call__`

The primary way to interact with an agent is by calling it as a function. The `__call__` method processes a natural language prompt through the agent's event loop.

```python
def __call__(
    self,
    prompt: AgentInput = None,
    *,
    invocation_state: dict[str, Any] | None = None,
    structured_output_model: type[BaseModel] | None = None,
    structured_output_prompt: str | None = None,
    **kwargs: Any,
) -> AgentResult:
```

[2]

This method returns an `AgentResult` object, which contains the final message from the model, the stop reason, and other metrics.

### 2.3. Streaming Responses: `stream_async`

For applications that require real-time output, the `stream_async` method provides an asynchronous iterator that yields events as they occur during the agent's execution.

```python
async def stream_async(
    self,
    prompt: AgentInput = None,
    *,
    invocation_state: dict[str, Any] | None = None,
    structured_output_model: type[BaseModel] | None = None,
    structured_output_prompt: str | None = None,
    **kwargs: Any,
) -> AsyncIterator[Any]:
```

[2]

### 2.4. Structured Output

The agent can be configured to produce structured output that conforms to a Pydantic model. This is achieved by passing a `structured_output_model` to the agent's invocation. The agent will then attempt to format its response according to the provided model [2].

## 3. The `strands.agent.agent.AgentResult` Class

The `AgentResult` class encapsulates the result of an agent invocation. It contains the following key attributes:

*   `stop_reason`: The reason why the agent loop terminated.
*   `message`: The final message from the model.
*   `metrics`: Performance metrics from the event loop.
*   `state`: The final state of the event loop.
*   `structured_output`: The parsed structured output, if a `structured_output_model` was specified [2].

## 4. Code Examples

The following code examples are extracted from the documentation:

```python
# Agent constructor
class Agent(AgentBase):
    def __init__(
        self,
        model: Model | str | None = None,
        messages: Messages | None = None,
        tools: list[Union[str, dict[str, str], "ToolProvider", Any]] | None = None,
        system_prompt: str | list[SystemContentBlock] | None = None,
        structured_output_model: type[BaseModel] | None = None,
        callback_handler: Callable[..., Any] | _DefaultCallbackHandlerSentinel | None = _DEFAULT_CALLBACK_HANDLER,
        conversation_manager: ConversationManager | None = None,
        record_direct_tool_call: bool = True,
        load_tools_from_directory: bool = False,
        trace_attributes: Mapping[str, AttributeValue] | None = None,
        *,
        agent_id: str | None = None,
        name: str | None = None,
        description: str | None = None,
        state: AgentState | dict | None = None,
        hooks: list[HookProvider] | None = None,
        session_manager: SessionManager | None = None,
        structured_output_prompt: str | None = None,
        tool_executor: ToolExecutor | None = None,
        retry_strategy: ModelRetryStrategy | _DefaultRetryStrategySentinel | None = _DEFAULT_RETRY_STRATEGY,
    ):
```

```python
# Agent invocation
def __call__(
    self,
    prompt: AgentInput = None,
    *,
    invocation_state: dict[str, Any] | None = None,
    structured_output_model: type[BaseModel] | None = None,
    structured_output_prompt: str | None = None,
    **kwargs: Any,
) -> AgentResult:
```

```python
# Streaming example
async for event in agent.stream_async("Analyze this data"):
    if "data" in event:
        yield event["data"]
```

## 5. Classes and Interfaces

The following is a list of the key classes and interfaces related to the Agent and Agent Loop:

*   `strands.agent.agent.Agent`
*   `strands.agent.agent.AgentBase`
*   `strands.agent.agent.AgentInput`
*   `strands.agent.agent.AgentState`
*   `strands.agent.agent.AgentResult`
*   `strands.agent.conversation_manager.ConversationManager`
*   `strands.agent.conversation_manager.SlidingWindowConversationManager`
*   `strands.hooks.events.AfterInvocationEvent`
*   `strands.hooks.events.HookEvent`

## 6. References

[1] Strands Agents Documentation. "Agent Loop". [https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-loop/index.md](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/agent-loop/index.md)

[2] Strands Agents Documentation. "strands.agent.agent". [https://strandsagents.com/latest/documentation/docs/api-reference/python/agent/agent/index.md](https://strandsagents.com/latest/documentation/docs/api-reference/python/agent/agent/index.md)
