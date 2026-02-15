# mitmproxy.connection

## ConnectionState

```python
class ConnectionState(enum.Flag):
    """The current state of the underlying socket."""

    CLOSED = 0
    CAN_READ = 1
    CAN_WRITE = 2
    OPEN = CAN_READ | CAN_WRITE
```

## Address Type

```python
Address = tuple[str, int]
```

Represents an IP address and port combination.

## TransportProtocol Type

```python
TransportProtocol = Literal["tcp", "udp"]
```

## TlsVersion Type

```python
TlsVersion = Literal[
    "SSLv3",
    "TLSv1",
    "TLSv1.1",
    "TLSv1.2",
    "TLSv1.3",
    "DTLSv0.9",
    "DTLSv1",
    "DTLSv1.2",
    "QUICv1",
]
```

## Connection

```python
@dataclass(kw_only=True)
class Connection(SerializableDataclass, metaclass=ABCMeta):
    """Base class for client and server connections.

    The connection object exposes metadata about the connection only,
    not the underlying socket object. All I/O is handled by
    mitmproxy.proxy.server exclusively.
    """
```

### Attributes

| Name | Type | Description |
|------|------|-------------|
| `peername` | `Address \| None` | Remote's (ip, port) tuple |
| `sockname` | `Address \| None` | Local (ip, port) tuple |
| `state` | `ConnectionState` | Current connection state (default: CLOSED) |
| `id` | `str` | Unique UUID identifier (auto-generated) |
| `transport_protocol` | `TransportProtocol` | Protocol in use (default: "tcp") |
| `error` | `str \| None` | Error description for this address |
| `tls` | `bool` | Whether TLS should be established (default: False) |
| `certificate_list` | `Sequence[Cert]` | TLS certificates from peer; first is end-entity |
| `alpn` | `bytes \| None` | Negotiated application-layer protocol |
| `alpn_offers` | `Sequence[bytes]` | ALPN offers from ClientHello |
| `cipher` | `str \| None` | Active cipher name from OpenSSL |
| `cipher_list` | `Sequence[str]` | Ciphers accepted by proxy server |
| `tls_version` | `TlsVersion \| None` | Active TLS version |
| `sni` | `str \| None` | Server Name Indication from ClientHello |
| `timestamp_start` | `float \| None` | Connection start timestamp |
| `timestamp_end` | `float \| None` | Connection close timestamp |
| `timestamp_tls_setup` | `float \| None` | TLS handshake completion timestamp |

### Properties

| Name | Type | Description |
|------|------|-------------|
| `connected` | `bool` | Read-only; True if state is OPEN |
| `tls_established` | `bool` | Read-only; True if TLS handshake completed |
| `alpn_proto_negotiated` | `bytes \| None` | **Deprecated:** Use `alpn` instead |

## Client

```python
@dataclass(eq=False, repr=False, kw_only=True)
class Client(Connection):
    """A connection between a client and mitmproxy."""
```

### Attributes

| Name | Type | Description |
|------|------|-------------|
| `peername` | `Address` | Client's address (required) |
| `sockname` | `Address` | Local address of receiving socket (required) |
| `mitmcert` | `Cert \| None` | Certificate mitmproxy uses with client |
| `proxy_mode` | `ProxyMode` | Proxy server type (default: regular) |
| `timestamp_start` | `float` | TCP SYN received timestamp (auto-set) |

### Properties

| Name | Type | Description |
|------|------|-------------|
| `address` | `Address` | **Deprecated:** Use `peername` |
| `cipher_name` | `str \| None` | **Deprecated:** Use `cipher` |
| `clientcert` | `Cert \| None` | **Deprecated:** Use `certificate_list[0]` |

## Server

```python
@dataclass(eq=False, repr=False, kw_only=True)
class Server(Connection):
    """A connection between mitmproxy and an upstream server."""
```

### Attributes

| Name | Type | Description |
|------|------|-------------|
| `address` | `Address \| None` | Server's (host, port) tuple; host is domain or IP |
| `peername` | `Address \| None` | Resolved (ip, port); set during connection establishment |
| `sockname` | `Address \| None` | Local (ip, port) tuple |
| `timestamp_start` | `float \| None` | Connection establishment start timestamp |
| `timestamp_tcp_setup` | `float \| None` | TCP ACK received timestamp |
| `via` | `ServerSpec \| None` | Optional upstream proxy specification |

### Properties

| Name | Type | Description |
|------|------|-------------|
| `ip_address` | `Address \| None` | **Deprecated:** Use `peername` |
| `cert` | `Cert \| None` | **Deprecated:** Use `certificate_list[0]` |

### Methods

| Name | Signature | Description |
|------|-----------|-------------|
| `__setattr__` | `(name: str, value: Any) -> None` | Prevents changing address/via on open connections |

---

**Module exports:** `["Connection", "Client", "Server", "ConnectionState"]`
