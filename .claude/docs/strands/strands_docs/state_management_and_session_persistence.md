# Strands Agents SDK: State Management and Session Persistence

This report provides a comprehensive overview of state management and session persistence within the Strands Agents SDK for Python. It covers the core concepts, classes, and implementation details necessary to build stateful and persistent agents.

## State Management

State management in the Strands Agents SDK is categorized into three distinct forms, each serving a specific purpose in maintaining context and data throughout the agent's lifecycle.

### Forms of State

| State Type | Description | Persistence | Accessibility |
| :--- | :--- | :--- | :--- |
| **Conversation History** | The sequence of messages exchanged between the user and the agent. | Across requests (managed by Conversation Manager) | `agent.messages` |
| **Agent State** | A key-value store for JSON-serializable data that needs to be maintained across multiple requests. | Across requests (managed by Session Manager) | `agent.state` |
| **Request State** | A dictionary for temporary data that is relevant only within a single request-response cycle. | Single request | `kwargs["request_state"]` in callbacks |

### Conversation History

The conversation history is the primary mechanism for maintaining the context of the interaction. It is directly accessible through the `agent.messages` attribute, which contains a list of all user and assistant messages, including tool calls and their results. The history can be initialized when creating an `Agent` instance to resume a previous conversation.

To manage the size of the conversation history and prevent it from exceeding the model's context window, the SDK utilizes a `ConversationManager`. The default implementation is the `SlidingWindowConversationManager`, which keeps a fixed number of recent messages and discards older ones.

### Agent State

Agent state provides a means to store and retrieve stateful information that is not part of the conversation history but needs to persist across multiple interactions. This is useful for storing user preferences, session data, or any other information that the agent needs to remember. The agent state is accessed through the `agent.state` object, which provides `get()`, `set()`, and `delete()` methods for interacting with the key-value store. It is important to note that all data stored in the agent state must be JSON-serializable.

### Request State

Request state is a more ephemeral form of state that is only available within a single agent invocation. It is a dictionary that can be used to pass data between different components of the agent's internal event loop, such as callback handlers. The request state is initialized at the beginning of each agent call and is returned in the `AgentResult` object.

## Session Persistence

Session persistence in the Strands Agents SDK allows agents to maintain their state and conversation history across multiple sessions and application restarts. This is achieved through the use of session managers, which are responsible for storing and retrieving session data from a persistent storage backend.

### SessionManager Abstract Base Class

The `SessionManager` is an abstract base class that defines the contract for all session managers. It provides a common interface for saving and loading session data, regardless of the underlying storage mechanism. To create a custom session manager, you would subclass `SessionManager` and implement its abstract methods.

### Built-in Session Managers

The SDK provides two built-in session managers for common use cases:

| Session Manager | Description | Storage Backend | Key Configuration Parameters |
| :--- | :--- | :--- | :--- |
| `FileSessionManager` | Persists session data to the local filesystem. | Local Filesystem | `session_id`, `storage_dir` |
| `S3SessionManager` | Persists session data to an Amazon S3 bucket. | Amazon S3 | `session_id`, `bucket`, `prefix`, `boto_session`, `region_name` |

### Custom Session Persistence

For more advanced scenarios, you can implement a custom session manager by creating a class that inherits from the `SessionManager` abstract base class. This allows you to integrate with any storage backend, such as a database or a key-value store. The `RepositorySessionManager` provides a convenient way to implement custom persistence by leveraging a `BaseRepository` for data access.

## Key Classes and Interfaces

The following table summarizes the key classes and interfaces involved in state management and session persistence in the Strands Agents SDK.

| Class/Interface | Import Path | Description |
| :--- | :--- | :--- |
| `Agent` | `strands.Agent` | The main class for creating and interacting with agents. It encapsulates the agent's state, conversation history, and tools. |
| `SlidingWindowConversationManager` | `strands.agent.conversation_manager.SlidingWindowConversationManager` | The default conversation manager that maintains a fixed-size window of the most recent messages. |
| `ToolContext` | `strands.ToolContext` | An object that provides access to the agent's context, including its state, within a tool's execution. |
| `SessionManager` | `strands.session.session_manager.SessionManager` | An abstract base class that defines the interface for session persistence. |
| `FileSessionManager` | `strands.session.file_session_manager.FileSessionManager` | A concrete implementation of `SessionManager` that persists session data to the local filesystem. |
| `S3SessionManager` | `strands.session.s3_session_manager.S3SessionManager` | A concrete implementation of `SessionManager` that persists session data to an Amazon S3 bucket. |
| `RepositorySessionManager` | `strands.session.repository_session_manager.RepositorySessionManager` | A session manager that uses a `BaseRepository` for persistence, enabling custom storage solutions. |
| `Session` | `strands.types.session.Session` | The Pydantic model representing the top-level session data. |
| `SessionAgent` | `strands.types.session.SessionAgent` | The Pydantic model representing agent-specific data within a session. |
| `SessionMessage` | `strands.types.session.SessionMessage` | The Pydantic model representing a single message within a session's conversation history. |

## Code Examples

This section provides a collection of code examples that demonstrate the concepts discussed in this report.

### State Management

**Accessing Conversation History**

```python
from strands import Agent

# Create an agent
agent = Agent()

# Send a message and get a response
agent("Hello!")

# Access the conversation history
print(agent.messages)  # Shows all messages exchanged so far
```

**Initializing an Agent with Existing Messages**

```python
from strands import Agent

# Create an agent with initial messages
agent = Agent(messages=[
    {"role": "user", "content": [{"text": "Hello, my name is Strands!"}]},
    {"role": "assistant", "content": [{"text": "Hi there! How can I help you today?"}]}
])

# Continue the conversation
agent("What's my name?")
```

**Using the `SlidingWindowConversationManager`**

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

# Create a conversation manager with custom window size
conversation_manager = SlidingWindowConversationManager(
    window_size=10,  # Maximum number of message pairs to keep
)

# Use the conversation manager with your agent
agent = Agent(conversation_manager=conversation_manager)
```

**Using Agent State**

```python
from strands import Agent

# Create an agent with initial state
agent = Agent(state={"user_preferences": {"theme": "dark"}, "session_count": 0})

# Access state values
theme = agent.state.get("user_preferences")
print(theme)  # {"theme": "dark"}

# Set new state values
agent.state.set("last_action", "login")
agent.state.set("session_count", 1)

# Get entire state
all_state = agent.state.get()
print(all_state)  # All state data as a dictionary

# Delete state values
agent.state.delete("last_action")
```

### Session Persistence

**Using the `FileSessionManager`**

```python
from strands import Agent
from strands.session.file_session_manager import FileSessionManager

# Create a session manager with a unique session ID
session_manager = FileSessionManager(session_id="test-session")

# Create an agent with the session manager
agent = Agent(session_manager=session_manager)

# Use the agent - all messages and state are automatically persisted
agent("Hello!")  # This conversation is persisted
```

**Using the `S3SessionManager`**

```python
from strands import Agent
from strands.session.s3_session_manager import S3SessionManager
import boto3

# Optional: Create a custom boto3 session
boto_session = boto3.Session(region_name="us-west-2")

# Create a session manager that stores data in S3
session_manager = S3SessionManager(
    session_id="user-456",
    bucket="my-agent-sessions",
    prefix="production/",  # Optional key prefix
    boto_session=boto_session,  # Optional boto3 session
    region_name="us-west-2"  # Optional AWS region (if boto_session not provided)
)

# Create an agent with the session manager
agent = Agent(session_manager=session_manager)

# Use the agent normally - state and messages will be persisted to S3
agent("Tell me about AWS S3")
```

## References

[1] Strands Agents Documentation. (2026). *State Management*. Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/state/index.md

[2] Strands Agents Documentation. (2026). *Session Management*. Retrieved from https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/session-management/index.md
