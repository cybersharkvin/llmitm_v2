# mitmproxy.flow

## Error

```python
@dataclass
class Error(serializable.SerializableDataclass)
```

Represents connection or protocol errors distinct from normal HTTP error responses. Indicates issues like interrupted connections, timeouts, or protocol failures.

### Attributes

- `msg: str` — Message describing the error
- `timestamp: float` — Unix timestamp when the error occurred (defaults to current time)
- `KILLED_MESSAGE: ClassVar[str]` — Class constant: `"Connection killed."`

### Methods

- `__str__()` — Returns the error message
- `__repr__()` — Returns the error message

---

## Flow

```python
class Flow(serializable.Serializable)
```

Base class for network flows. A flow represents a collection of protocol objects, such as HTTP request/response pairs or TCP messages.

**Related types:** `mitmproxy.http.HTTPFlow`, `mitmproxy.tcp.TCPFlow`, `mitmproxy.udp.UDPFlow`

### Attributes

- `client_conn: connection.Client` — The client connected to mitmproxy
- `server_conn: connection.Server` — The server mitmproxy connected to (may have `timestamp_start = None` if no server connection was made)
- `error: Error | None` — Connection or protocol error affecting this flow
- `intercepted: bool` — Whether the flow is paused pending user action
- `marked: str` — User marking annotation (single character or emoji name like `:grapes:`)
- `is_replay: str | None` — Indicates replay status: `"request"` or `"response"`, or `None`
- `live: bool` — `True` for active connections; `False` for completed/loaded flows
- `timestamp_created: float` — Unix timestamp of flow creation (unchanged on replay)
- `id: str` — Unique flow identifier
- `comment: str` — User comment
- `type: ClassVar[str]` — Flow type identifier (e.g., `"http"`, `"tcp"`, `"dns"`)

### Methods

#### Lifecycle Management

```python
def copy(self) -> Flow
```
Creates a copy of the flow with `live` set to `False`.

```python
def backup(self, force: bool = False) -> None
```
Saves a backup of the current flow state for restoration via `revert()`.

```python
def revert(self) -> None
```
Restores the flow to its last backed-up state.

```python
def modified(self) -> bool
```
Returns `True` if the flow has been modified by the user since backup.

#### Flow Control

```python
def intercept(self) -> None
```
Pauses the flow until `resume()` is called.

```python
async def wait_for_resume(self) -> None
```
Asynchronously waits until the flow is resumed.

```python
def resume(self) -> None
```
Continues processing after an `intercept()`.

#### Termination

```python
@property
def killable(self) -> bool
```
Read-only. Returns `True` if the flow can be killed, `False` otherwise.

```python
def kill(self) -> None
```
Terminates the flow so the request/response is not forwarded. Raises `ControlException` if not killable.

#### Serialization

```python
def get_state(self) -> serializable.State
```
Returns the flow's serializable state dictionary.

```python
def set_state(self, state: serializable.State) -> None
```
Restores the flow from a state dictionary.

```python
@classmethod
def from_state(cls, state: serializable.State) -> Flow
```
Reconstructs a flow of the appropriate type from a state dictionary.

#### Timing

```python
@property
def timestamp_start(self) -> float
```
Read-only. Start timestamp of the flow (alias for `client_conn.timestamp_start` or `Request.timestamp_start` depending on flow type).
