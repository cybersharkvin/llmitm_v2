# mitmproxy.tcp

## Classes

### TCPMessage

Represents an individual TCP message unit.

**Important Note:** "TCP is *stream-based* and not *message-based*. For practical purposes the stream is chunked into messages here, but you should not rely on message boundaries."

#### Constructor

```python
TCPMessage(from_client, content, timestamp=None)
```

**Parameters:**
- `from_client`: Boolean indicating message direction (client-to-server)
- `content`: The message payload data
- `timestamp`: Unix timestamp; defaults to current time if not provided

####Properties

- `from_client`: Direction indicator for the message
- `content`: Message payload
- `timestamp`: When the message was transmitted

#### Methods

```python
@classmethod
from_state(cls, state) -> TCPMessage
```
Deserialize from state tuple.

```python
get_state() -> tuple
```
Returns: `(from_client, content, timestamp)`

```python
set_state(state: tuple) -> None
```
Restore instance from state tuple.

```python
__repr__() -> str
```
String representation showing direction and content.

---

### TCPFlow

Simplified representation of a TCP session.

#### Constructor

```python
TCPFlow(
    client_conn: mitmproxy.connection.Client,
    server_conn: mitmproxy.connection.Server,
    live: bool = False
)
```

**Parameters:**
- `client_conn`: Client connection details
- `server_conn`: Server connection details
- `live`: Whether connection is active

#### Properties

```python
messages: list[TCPMessage]
```
Transmitted messages over this connection. Access latest via `flow.messages[-1]` in event hooks.

```python
type: ClassVar[str] = 'tcp'
```
The flow protocol type identifier.

#### Methods

```python
get_state() -> serializable.State
```
Serialize flow and all messages to state dictionary.

```python
set_state(state: serializable.State) -> None
```
Restore flow from serialized state.

```python
__repr__() -> str
```
Returns: `<TCPFlow (n messages)>` format string.

#### Inherited Members

TCPFlow inherits from `mitmproxy.flow.Flow`, providing properties like `client_conn`, `server_conn`, `error`, `intercepted`, `marked`, `live`, `timestamp_created`, `id`, `metadata`, `comment` and methods including `copy()`, `kill()`, `intercept()`, `resume()`.
