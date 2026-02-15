# mitmproxy.proxy.mode_specs

## Overview

This module parses proxy mode specifications with the general syntax:

```
mode [: mode_configuration] [@ [listen_addr:]listen_port]
```

## Constants

```python
TCP: Literal["tcp", "udp", "both"] = "tcp"
UDP: Literal["tcp", "udp", "both"] = "udp"
BOTH: Literal["tcp", "udp", "both"] = "both"
```

## ProxyMode

Base class for all proxy mode implementations.

### Attributes

- `full_spec: str` — Complete proxy mode specification as entered by the user
- `data: str` — Raw mode data (portion after the mode name)
- `custom_listen_host: str | None` — Custom listen host from spec, if provided
- `custom_listen_port: int | None` — Custom listen port from spec, if provided
- `type_name: ClassVar[str]` — Unique mode identifier (e.g., "regular", "reverse")

### Properties

```python
@property
def description(self) -> str:
    """Mode description for server logs and UI."""

@property
def default_port(self) -> int | None:
    """Default listen port (8080 by default)."""

@property
def transport_protocol(self) -> Literal["tcp", "udp", "both"]:
    """Transport protocol used by this mode's server."""
```

### Methods

```python
@classmethod
@cache
def parse(cls, spec: str) -> Self:
    """Parse a proxy mode specification string into a ProxyMode instance."""

def listen_host(self, default: str | None = None) -> str:
    """
    Determine listen address. Returns custom host from spec, falls back to
    provided default, or empty string for all hosts.
    """

def listen_port(self, default: int | None = None) -> int | None:
    """
    Determine listen port. Returns custom port from spec, provided default,
    or default_port property.
    """

@classmethod
def from_state(cls, state):
    """Deserialize from state."""

def get_state(self):
    """Serialize to state."""

def set_state(self, state):
    """Restore state (raises FrozenInstanceError if modified)."""
```

## Concrete Implementations

### RegularMode

```python
class RegularMode(ProxyMode):
    """HTTP(S) proxy using HTTP CONNECT calls or absolute-form requests."""
    description = "HTTP(S) proxy"
    transport_protocol = "tcp"
    default_port = 8080
```

### TransparentMode

```python
class TransparentMode(ProxyMode):
    """Transparent proxy implementation."""
    description = "Transparent Proxy"
    transport_protocol = "tcp"
    default_port = 8080
```

### UpstreamMode

```python
class UpstreamMode(ProxyMode):
    """HTTP(S) proxy forwarding all connections through an upstream proxy."""
    description = "HTTP(S) proxy (upstream mode)"
    transport_protocol = "tcp"
    default_port = 8080

    scheme: Literal["http", "https"]
    address: tuple[str, int]
```

### ReverseMode

```python
class ReverseMode(ProxyMode):
    """
    Reverse proxy acting as a normal server while redirecting requests
    to a fixed target.
    """
    description = "reverse proxy"
    transport_protocol = "tcp" | "udp" | "both"
    default_port = 8080 | 53

    scheme: Literal["http", "https", "http3", "tls", "dtls", "tcp", "udp", "dns", "quic"]
    address: tuple[str, int]

    @property
    def default_port(self) -> int | None:
        """Returns 53 for DNS scheme, else 8080."""
```

### Socks5Mode

```python
class Socks5Mode(ProxyMode):
    """SOCKSv5 proxy server."""
    description = "SOCKS v5 proxy"
    transport_protocol = "tcp"
    default_port = 1080
```

### DnsMode

```python
class DnsMode(ProxyMode):
    """DNS server."""
    description = "DNS server"
    transport_protocol = "both"
    default_port = 53
```

### WireGuardMode

```python
class WireGuardMode(ProxyMode):
    """WireGuard-based proxy server."""
    description = "WireGuard server"
    transport_protocol = "udp"
    default_port = 51820
```

### LocalMode

```python
class LocalMode(ProxyMode):
    """OS-level transparent proxy."""
    description = "Local redirector"
    transport_protocol = "both"
    default_port = None
```

### TunMode

```python
class TunMode(ProxyMode):
    """TUN interface for system-level packet interception."""
    description = "TUN interface"
    transport_protocol = "both"
    default_port = None
```

### OsProxyMode

```python
class OsProxyMode(ProxyMode):
    """Deprecated alias for LocalMode."""
    # Raises ValueError on initialization
```
