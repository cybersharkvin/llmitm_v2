# mitmproxy.udp

## Classes

### UDPMessage

Represents an individual UDP datagram.

```python
class UDPMessage(mitmproxy.coretypes.serializable.Serializable)
```

#### Constructor

```python
UDPMessage(from_client, content, timestamp=None)
```

**Parameters:**
- `from_client`: Boolean indicating message direction
- `content`: The datagram payload
- `timestamp`: Optional timestamp (defaults to current time)

#### Properties

- `from_client`: Indicates if the message originated from the client
- `content`: The datagram data
- `timestamp`: When the datagram was transmitted

#### Methods

- `from_state(cls, state)`: Class method to reconstruct from serialized state
- `get_state()`: Returns serializable state tuple
- `set_state(state)`: Updates instance from serialized state
- `__repr__()`: String representation showing direction and content

---

### UDPFlow

Represents a UDP session containing multiple datagrams.

```python
class UDPFlow(mitmproxy.flow.Flow)
```

#### Constructor

```python
UDPFlow(
    client_conn: mitmproxy.connection.Client,
    server_conn: mitmproxy.connection.Server,
    live: bool = False
)
```

**Parameters:**
- `client_conn`: Client connection details
- `server_conn`: Server connection details
- `live`: Whether this is an active session

#### Properties

- `messages`: List of `UDPMessage` objects transmitted over the connection
- `type`: Class variable set to `'udp'` identifying the flow type

#### Methods

- `get_state()`: Returns serialized flow state dictionary
- `set_state(state)`: Restores flow from serialized state
- `__repr__()`: Returns string showing message count

#### Inherited Members

Inherits all members from `mitmproxy.flow.Flow`, including connection management, state tracking, interception control, and metadata handling.
