# mitmproxy.websocket

## Overview

The mitmproxy.websocket module provides classes for representing individual WebSocket messages and their container. WebSocket connections are now represented as HTTP flows with the `mitmproxy.http.HTTPFlow.websocket` attribute set.

## Type Aliases

```python
WebSocketMessageState = tuple[int, bool, bytes, float, bool, bool]
```

Represents the serializable state of a WebSocket message.

## Classes

### WebSocketMessage

A single WebSocket message exchanged between peers.

**Description:** "Fragmented WebSocket messages are reassembled by mitmproxy and then represented as a single instance of this class." All message contents are stored as bytes to avoid type confusion issues.

#### Attributes

- `from_client: bool` — Indicates whether the message originated from the client
- `type: Opcode` — Message type per RFC 6455 opcode specification (TEXT or BINARY frames)
- `content: bytes` — The message payload as bytes
- `timestamp: float` — When the message was received or created
- `dropped: bool` — Whether the message was blocked from forwarding
- `injected: bool` — Whether the message was artificially created rather than from client/server

#### Constructor

```python
def __init__(
    type: int | Opcode,
    from_client: bool,
    content: bytes,
    timestamp: float | None = None,
    dropped: bool = False,
    injected: bool = False
) -> None
```

#### Properties

```python
@property
def is_text(self) -> bool
```

Returns `True` for TEXT frames, `False` for BINARY frames.

```python
@property
def text(self) -> str
```

Accesses message content as decoded text. Only available when `is_text` is `True`. Raises `AttributeError` otherwise.

#### Methods

```python
def drop(self) -> None
```

Prevents forwarding of this message to the other peer.

```python
def kill(self) -> None
```

Deprecated alias for `drop()`. Issues a `DeprecationWarning`.

```python
@classmethod
def from_state(cls, state: WebSocketMessageState) -> WebSocketMessage
```

Reconstructs a message from its serialized state.

```python
def get_state(self) -> WebSocketMessageState
```

Returns the serialized state tuple.

```python
def set_state(self, state: WebSocketMessageState) -> None
```

Updates the message from a serialized state tuple.

---

### WebSocketData

A container for all data related to a single WebSocket connection.

**Description:** "A data container for everything related to a single WebSocket connection. This is typically accessed as mitmproxy.http.HTTPFlow.websocket."

#### Attributes

- `messages: list[WebSocketMessage]` — All messages transferred over the connection
- `closed_by_client: bool | None` — `True` if client closed, `False` if server closed, `None` if active
- `close_code: int | None` — RFC 6455 close code value
- `close_reason: str | None` — RFC 6455 close reason text
- `timestamp_end: float | None` — Timestamp when the connection was closed

#### Constructor

```python
def __init__(
    messages: list[WebSocketMessage] = <factory>,
    closed_by_client: bool | None = None,
    close_code: int | None = None,
    close_reason: str | None = None,
    timestamp_end: float | None = None
)
```
