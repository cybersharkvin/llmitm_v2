# mitmproxy.http

## Headers

```python
class Headers(multidict.MultiDict)
```

A case-insensitive header container supporting both convenient access and raw data manipulation.

### Constructor

```python
def __init__(
    self,
    fields: Iterable[tuple[bytes, bytes]] = (),
    **headers
)
```

Create headers with keyword arguments or from byte tuples. Header names with underscores are converted to dashes.

### Methods

```python
def get_all(name: str | bytes) -> list[str]
```

Retrieve all values for a header without folding multiple entries.

```python
def set_all(name: str | bytes, values: Iterable[str | bytes])
```

Explicitly set multiple header values.

```python
def insert(index: int, key: str | bytes, value: str | bytes)
```

Insert a header at a specific position.

```python
def items(multi=False)
```

Return header items. If `multi=True`, returns all fields including duplicates.

### Properties

```python
fields: tuple[tuple[bytes, bytes], ...]
```

Raw header field tuples as bytes.

---

## Message

```python
class Message(serializable.Serializable)
```

Base class for Request and Response.

### Properties

```python
http_version: str
```

HTTP version string (e.g., "HTTP/1.1").

```python
is_http10: bool
is_http11: bool
is_http2: bool
is_http3: bool
```

Protocol version checkers.

```python
headers: Headers
```

The HTTP headers.

```python
trailers: Headers | None
```

HTTP trailers (see RFC 7230).

```python
raw_content: bytes | None
```

The raw (potentially compressed) message body. Returns `None` if missing.

```python
content: bytes | None
```

The uncompressed message body as bytes.

```python
text: str | None
```

The uncompressed and decoded message body as text.

```python
timestamp_start: float
timestamp_end: float | None
```

Timestamps for header receipt and last byte received.

```python
stream: Callable[[bytes], Iterable[bytes] | bytes] | bool = False
```

Controls message body streaming behavior.

### Methods

```python
def set_content(value: bytes | None) -> None
```

Set the message body, handling encoding automatically.

```python
def get_content(strict: bool = True) -> bytes | None
```

Retrieve message body, optionally returning compressed content on error.

```python
def set_text(text: str | None) -> None
```

Set the message body from a text string.

```python
def get_text(strict: bool = True) -> str | None
```

Retrieve message body as decoded text, with fallback handling.

```python
def decode(strict: bool = True) -> None
```

Decompress body based on Content-Encoding header.

```python
def encode(encoding: str) -> None
```

Compress body with specified encoding (gzip, deflate, identity, br, zstd).

```python
def json(**kwargs) -> Any
```

Parse message body as JSON.

---

## Request

```python
class Request(Message)
```

Represents an HTTP request.

### Constructor

```python
def __init__(
    self,
    host: str,
    port: int,
    method: bytes,
    scheme: bytes,
    authority: bytes,
    path: bytes,
    http_version: bytes,
    headers: Headers | tuple[tuple[bytes, bytes], ...],
    content: bytes | None,
    trailers: Headers | tuple[tuple[bytes, bytes], ...] | None,
    timestamp_start: float,
    timestamp_end: float | None,
)
```

### Factory Method

```python
@classmethod
def make(
    cls,
    method: str,
    url: str,
    content: bytes | str = "",
    headers: Headers | dict[str | bytes, str | bytes] | Iterable[tuple[bytes, bytes]] = (),
) -> Request
```

Simplified API for creating request objects.

### Properties

```python
first_line_format: str
```

Request format: "authority", "absolute", or "relative".

```python
method: str
```

HTTP method (e.g., "GET").

```python
scheme: str
```

Request scheme ("http" or "https").

```python
authority: str
```

Request authority portion.

```python
host: str
```

Target server hostname or IP.

```python
host_header: str | None
```

The Host/authority header value.

```python
port: int
```

Target port number.

```python
path: str
```

Request path including query string.

```python
url: str
```

Full URL constructed from scheme, host, port, and path.

```python
pretty_host: str
```

Host value, preferring the Host header (read-only).

```python
pretty_url: str
```

URL using pretty_host instead of host (read-only).

```python
query: multidict.MultiDictView[str, str]
```

Query parameters as a mutable mapping view.

```python
cookies: multidict.MultiDictView[str, str]
```

Request cookies as a mutable mapping view.

```python
path_components: tuple[str, ...]
```

URL path segments as unquoted strings (read-only).

```python
urlencoded_form: multidict.MultiDictView[str, str]
```

URL-encoded form data as a mutable mapping view.

```python
multipart_form: multidict.MultiDictView[bytes, bytes]
```

Multipart form data as a mutable mapping view.

### Methods

```python
def anticache() -> None
```

Remove headers that might produce cached responses.

```python
def anticomp() -> None
```

Set Accept-Encoding to only accept uncompressed responses.

```python
def constrain_encoding() -> None
```

Limit permissible Accept-Encoding values to supported decodings.

---

## Response

```python
class Response(Message)
```

Represents an HTTP response.

### Constructor

```python
def __init__(
    self,
    http_version: bytes,
    status_code: int,
    reason: bytes,
    headers: Headers | tuple[tuple[bytes, bytes], ...],
    content: bytes | None,
    trailers: None | Headers | tuple[tuple[bytes, bytes], ...],
    timestamp_start: float,
    timestamp_end: float | None,
)
```

### Factory Method

```python
@classmethod
def make(
    cls,
    status_code: int = 200,
    content: bytes | str = b"",
    headers: Headers | Mapping[str, str | bytes] | Iterable[tuple[bytes, bytes]] = (),
) -> Response
```

Simplified API for creating response objects.

### Properties

```python
status_code: int
```

HTTP status code (e.g., 200).

```python
reason: str
```

HTTP reason phrase (e.g., "Not Found"). Empty for HTTP/2.

```python
cookies: multidict.MultiDictView[str, tuple[str, multidict.MultiDict[str, str | None]]]
```

Response cookies with attributes (read-only values without reassignment).

### Methods

```python
def refresh(now=None) -> None
```

Refresh response for replay by adjusting date, expires, and cookie expiration headers.

---

## HTTPFlow

```python
class HTTPFlow(flow.Flow)
```

A collection of objects representing a single HTTP transaction.

### Attributes

```python
request: Request
```

The client's HTTP request.

```python
response: Response | None = None
```

The server's HTTP response.

```python
error: flow.Error | None = None
```

Connection or protocol error affecting this flow.

```python
websocket: mitmproxy.websocket.WebSocketData | None = None
```

WebSocket data if the HTTP flow initiated a WebSocket connection.

### Properties

```python
timestamp_start: float
```

Read-only alias for request timestamp start.

### Methods

```python
def copy()
```

Create a deep copy of this flow.
