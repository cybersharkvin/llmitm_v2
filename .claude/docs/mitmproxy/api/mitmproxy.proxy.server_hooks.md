# mitmproxy.proxy.server_hooks

## Classes

### ClientConnectedHook

```python
@dataclass
class ClientConnectedHook(commands.StartHook):
```

"A client has connected to mitmproxy. Note that a connection can correspond to multiple HTTP requests."

Setting `client.error` terminates the connection.

**Attributes:**
- `client: connection.Client`

### ClientDisconnectedHook

```python
@dataclass
class ClientDisconnectedHook(commands.StartHook):
```

"A client connection has been closed (either by us or the client)."

**Attributes:**
- `client: connection.Client`

### ServerConnectionHookData

```python
@dataclass
class ServerConnectionHookData:
```

Event data for server connection event hooks.

**Attributes:**
- `server: connection.Server` — The server connection this hook is about
- `client: connection.Client` — The client on the other end

### ServerConnectHook

```python
@dataclass
class ServerConnectHook(commands.StartHook):
```

"Mitmproxy is about to connect to a server. Note that a connection can correspond to multiple requests."

Setting `data.server.error` terminates the connection.

**Attributes:**
- `data: ServerConnectionHookData`

### ServerConnectedHook

```python
@dataclass
class ServerConnectedHook(commands.StartHook):
```

"Mitmproxy has connected to a server."

**Attributes:**
- `data: ServerConnectionHookData`

### ServerDisconnectedHook

```python
@dataclass
class ServerDisconnectedHook(commands.StartHook):
```

"A server connection has been closed (either by us or the server)."

**Attributes:**
- `data: ServerConnectionHookData`

### ServerConnectErrorHook

```python
@dataclass
class ServerConnectErrorHook(commands.StartHook):
```

"Mitmproxy failed to connect to a server. Every server connection will receive either a server_connected or a server_connect_error event, but not both."

**Attributes:**
- `data: ServerConnectionHookData`
