# mitmproxy.contentviews

## Overview

The contentviews module provides a framework for formatting, decoding, highlighting, and reencoding data. While primarily used for HTTP message bodies, these views can process data from various contexts including WebSocket and DNS messages.

## Classes

### Contentview

A runtime-checkable protocol defining the base interface for all content views.

```python
@typing.runtime_checkable
class Contentview(typing.Protocol):
```

**Properties:**

- `name: str` — The display name of the contentview (e.g., "XML/HTML"), inferred from class name by default
- `syntax_highlight: SyntaxHighlight` — Optional syntax highlighting format for prettified output; defaults to "none"

**Methods:**

```python
@abstractmethod
def prettify(
    self,
    data: bytes,
    metadata: Metadata,
) -> str:
```
Transforms raw data into human-readable format. May raise exceptions like `ValueError` if transformation fails.

```python
def render_priority(
    self,
    data: bytes,
    metadata: Metadata,
) -> float:
```
Returns a priority score for rendering the given data. Higher values indicate better suitability; return values below 0 indicate unsupported data. Defaults to 0.

---

### InteractiveContentview

A runtime-checkable protocol for contentviews supporting interactive editing and re-encoding.

```python
@typing.runtime_checkable
class InteractiveContentview(Contentview, typing.Protocol):
```

**Methods:**

```python
@abstractmethod
def reencode(
    self,
    prettified: str,
    metadata: Metadata,
) -> bytes:
```
Converts modified prettified output back into the original data format. May raise exceptions if re-encoding fails.

---

### Metadata

A dataclass containing contextual information about data being prettified.

```python
@dataclass
class Metadata:
```

**Attributes:**

- `flow: mitmproxy.flow.Flow | None` — Associated flow, if any
- `content_type: str | None` — HTTP content type, if available
- `http_message: mitmproxy.http.Message | None` — Parent HTTP message, if applicable
- `tcp_message: mitmproxy.tcp.TCPMessage | None` — Parent TCP message, if applicable
- `udp_message: mitmproxy.udp.UDPMessage | None` — Parent UDP message, if applicable
- `websocket_message: mitmproxy.websocket.WebSocketMessage | None` — Parent WebSocket message, if applicable
- `dns_message: mitmproxy.dns.DNSMessage | None` — Parent DNS message, if applicable
- `protobuf_definitions: pathlib.Path | None` — Path to .proto file for Protobuf field resolution
- `original_data: bytes | None` — Original unmodified data when re-encoding

---

## Type Aliases

### SyntaxHighlight

```python
type SyntaxHighlight = Literal[
    'css',
    'javascript',
    'xml',
    'yaml',
    'none',
    'error'
]
```

Supported syntax highlighting formats. Note: YAML is a superset of JSON; use YAML for JSON highlighting.

---

## Functions

### add()

```python
def add(
    contentview: Contentview | type[Contentview]
) -> None:
```

Registers a contentview for use in mitmproxy. Accepts either a `Contentview` instance or its class; when passing a class, the constructor is invoked with no arguments.
