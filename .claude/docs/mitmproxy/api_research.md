# mitmproxy Python API Research

> Comprehensive inventory from exhaustive exploration of the mitmproxy documentation and source code. Covers capabilities, APIs, and patterns useful for building Python-based traffic analysis tools.

---

## Key Insights for LLMitM v2

This is gold. Here's what jumps out for our problem:

### For the recon tools rewrite:

1. **`FlowReader` + `flow.get_state()`** — we can read every flow into a Python dict with full structure (headers, body, cookies, status, URL, TLS info) without any CLI subprocess or output parsing
2. **`flowfilter.parse()` + `flowfilter.match()`** — programmatic filtering, no CLI string mangling
3. **`request.json()`** — direct JSON parsing on flow bodies
4. **`request.query`** — parsed query params as multidict
5. **`request.cookies` / `response.cookies`** — parsed cookies directly
6. **`request.urlencoded_form` / `request.multipart_form`** — parsed form data
7. **Connection metadata** — `server_conn.certificate_list`, `client_conn.sni`, `tls_version`, `alpn`, `cipher` — richer fingerprinting data than we currently extract

### For bounded tool output:

Instead of piping through mitmdump CLI and truncating text, we can build tools that read flows with `FlowReader`, extract exactly the fields needed, and return structured, bounded JSON. Each tool controls exactly what goes into the agent's context.

### Bonus finds:
- **`flow.response.refresh()`** — updates date/expires/cookie timestamps for replay freshness
- **Sticky cookies/auth** — `stickycookie` option automatically replays session cookies, which is exactly what our `ExecutionContext.cookies` does manually
- **`Response.make()`** — factory for mock responses, useful for testing

### The path forward:
Replace the single `mitmdump` CLI tool with 3-4 Python tools that use `FlowReader`, `flowfilter`, and the HTTPFlow API directly.

### What is FlowReader?

It's just a deserializer. The `.mitm` file is a binary stream of serialized `Flow` objects (using tnetstring format). `FlowReader` opens that file and yields them back as Python objects one at a time:

```python
from mitmproxy.io import FlowReader

with open("capture.mitm", "rb") as f:
    for flow in FlowReader(f).stream():
        # flow is a fully hydrated HTTPFlow object
```

That's it. It's `json.load()` but for mitmproxy's binary format. No proxy running, no subprocess, no network — just reading a file and getting objects back.

The CLI command `mitmdump -nr capture.mitm --flow-detail 3` is literally just doing `FlowReader` -> format as text -> print to stdout. We've been shelling out to mitmdump to get a lossy text representation of data that's already structured.

Even without an agent, mitmproxy/dump can run uninterrupted against a target, and when traffic flows through, every request/response pair gets serialized as a `Flow` object into the binary `.mitm` file — headers, body, cookies, TLS info, timestamps, connection metadata, everything. Structured and complete, not text logs.

Then later you open it with `FlowReader` and get back fully hydrated Python objects:

```python
with open("capture.mitm", "rb") as f:
    for flow in FlowReader(f).stream():
        flow.request.method      # "POST"
        flow.request.pretty_url  # "http://localhost:3000/rest/user/login"
        flow.request.json()      # {"email": "admin@juice-sh.op", "password": "admin123"}
        flow.request.cookies     # MultiDict of cookies
        flow.response.status_code # 200
        flow.response.json()     # {"authentication": {"token": "eyJ..."}}
        flow.response.cookies    # Set-Cookie values parsed
        flow.response.headers    # case-insensitive multidict
```

No parsing, no regex, no truncation. The `.mitm` file IS the structured format.

### The irony in our codebase:

`fingerprint_from_mitm()` in `capture/launcher.py` already uses `FlowReader` to get structured flow objects... then **converts them back to text** (`>>> GET /path HTTP/1.1`) so the `Fingerprinter` can regex-parse them again.

The whole pipeline for the recon tools should just be: `FlowReader` -> access the attributes directly -> return bounded JSON to the agent. No text formatting, no CLI, no re-parsing.

---

## 1. Flow Reading/Writing API (mitmproxy.io)

### FlowReader
**Purpose**: Read flows from `.mitm` files (mitmproxy's native binary format) or HAR files.

**Key Methods**:
- `__init__(fo: BinaryIO)` - Initialize with a file object
- `stream() -> Iterable[flow.Flow]` - Generator that yields Flow objects

**File Format Detection**:
- Automatically detects HAR format (JSON starting with `{`)
- Falls back to tnetstring format (mitmproxy native binary)
- Handles BOM (Byte Order Mark) from Fiddler exports

### FlowWriter
**Purpose**: Write flows to mitmproxy's native binary format.

**Key Methods**:
- `__init__(fo: BinaryIO)` - Initialize with a file object
- `add(f: flow.Flow)` - Write a single flow

### FilteredFlowWriter
**Purpose**: Write flows with filter expression applied.

**Key Methods**:
- `__init__(fo: BinaryIO, flt: flowfilter.TFilter | None)`
- `add(f: flow.Flow)` - Only writes if flow matches filter

### Helper Function
- `read_flows_from_paths(paths) -> list[flow.Flow]` - Bulk read from multiple files

---

## 2. HTTPFlow Object Structure

### HTTPFlow Class (mitmproxy.http.HTTPFlow)
**Inherits from**: `flow.Flow`

**Core Attributes**:
- `request: Request` - The client's HTTP request (always present)
- `response: Response | None` - The server's HTTP response (may be None)
- `error: flow.Error | None` - Connection/protocol errors
- `websocket: WebSocketData | None` - WebSocket data if connection upgraded
- `client_conn: connection.Client` - Client connection metadata
- `server_conn: connection.Server` - Server connection metadata
- `id: str` - Unique UUID for this flow
- `intercepted: bool` - Flow is paused waiting for user action
- `marked: str` - User marker annotation
- `is_replay: str | None` - "request" or "response" if replayed
- `live: bool` - Flow belongs to active connection
- `timestamp_created: float` - Unix timestamp of creation
- `metadata: dict[str, Any]` - Arbitrary metadata storage
- `comment: str` - User comment

**Methods**:
- `get_state() -> dict` - Serialize to dictionary
- `set_state(state: dict)` - Deserialize from dictionary
- `copy() -> HTTPFlow` - Deep copy (sets `live=False`)

---

## 3. Request Object (mitmproxy.http.Request)

### Core Attributes
**URL Components**:
- `method: str` - HTTP method (e.g., "GET", "POST")
- `scheme: str` - "http" or "https"
- `host: str` - Target hostname or IP
- `port: int` - Target port
- `authority: str` - HTTP/2 :authority pseudo-header
- `path: str` - Path + query string (e.g., "/index.html?a=b")
- `url: str` - Full URL (computed from above, can be set)
- `pretty_host: str` - Host from Host header (preferred in transparent mode)
- `pretty_url: str` - URL using pretty_host

**Message Components** (inherited from Message):
- `http_version: str` - "HTTP/1.1", "HTTP/2.0", "HTTP/3"
- `headers: Headers` - Request headers (multidict)
- `trailers: Headers | None` - HTTP trailers
- `raw_content: bytes | None` - Raw (possibly compressed) body
- `content: bytes | None` - Decompressed body
- `text: str | None` - Decoded text body
- `timestamp_start: float` - Headers received timestamp
- `timestamp_end: float | None` - Last byte received timestamp

**Properties**:
- `is_http10 / is_http11 / is_http2 / is_http3: bool`
- `host_header: str | None` - Host or :authority header value
- `query: multidict.MultiDictView` - Parsed query parameters
- `cookies: multidict.MultiDictView` - Parsed cookies
- `urlencoded_form: multidict.MultiDictView | None` - Parsed form data
- `multipart_form: multidict.MultiDictView | None` - Parsed multipart data

### Key Methods
- `Request.make(method, url, content="", headers={})` - Factory method
- `decode(strict=True)` - Decompress content, remove Content-Encoding header
- `encode(encoding)` - Compress content (gzip, deflate, br, zstd)
- `json(**kwargs) -> Any` - Parse JSON body
- `get_content(strict=True) -> bytes | None` - Get decompressed content
- `get_text(strict=True) -> str | None` - Get decoded text
- `set_content(value: bytes | None)` - Set content, update headers
- `set_text(value: str | None)` - Set text content, auto-encode

---

## 4. Response Object (mitmproxy.http.Response)

### Core Attributes
- `status_code: int` - HTTP status code (e.g., 200, 404)
- `reason: str` - Reason phrase (e.g., "OK", "Not Found")
- `http_version: str` - HTTP version
- `headers: Headers` - Response headers
- `trailers: Headers | None` - HTTP trailers
- `raw_content: bytes | None` - Raw body
- `content: bytes | None` - Decompressed body
- `text: str | None` - Decoded text body
- `timestamp_start: float` - Headers received timestamp
- `timestamp_end: float | None` - Last byte received timestamp

**Properties**:
- `cookies: multidict.MultiDictView` - Parsed Set-Cookie headers

### Key Methods
- `Response.make(status_code=200, content=b"", headers={})` - Factory
- `decode(strict=True)` - Decompress content
- `encode(encoding)` - Compress content
- `json(**kwargs) -> Any` - Parse JSON body
- `refresh(now=None)` - Update timestamps for replay (date, expires, cookies)
- `get_content(strict=True) -> bytes | None`
- `get_text(strict=True) -> str | None`
- `set_content(value: bytes | None)`
- `set_text(value: str | None)`

---

## 5. Headers API (mitmproxy.http.Headers)

**Inherits from**: `multidict.MultiDict`

### Core Features
- **Case-insensitive**: `h["Host"]` == `h["host"]`
- **Multi-value support**: Multiple headers with same name
- **RFC 7230 folding**: Multiple values joined with ", "

### Key Methods
- `__getitem__(key) -> str` - Get folded value
- `__setitem__(key, value)` - Replace all headers with this name
- `__delitem__(key)` - Remove all headers with this name
- `get_all(key) -> list[str]` - Get all values (for Set-Cookie)
- `set_all(key, values)` - Set multiple headers with same name
- `insert(index, key, value)` - Insert at specific position
- `items(multi=False)` - Iterate (multi=True for all individual headers)

---

## 6. Connection Metadata

### Client Connection (mitmproxy.connection.Client)
- `peername: (str, int)` - Client's (IP, port)
- `tls: bool` - TLS should be established
- `tls_established: bool` - TLS is established
- `tls_version: TlsVersion | None` - "TLSv1.2", "TLSv1.3", etc.
- `sni: str | None` - Server Name Indication from ClientHello
- `alpn: bytes | None` - Negotiated protocol (b"h2", b"http/1.1")
- `cipher: str | None` - Active cipher name
- `certificate_list: Sequence[Cert]` - Client certs (for mTLS)

### Server Connection (mitmproxy.connection.Server)
- `address: (str, int) | None` - Target (host, port)
- `peername: (str, int) | None` - Resolved (IP, port)
- `tls_version: TlsVersion | None`
- `sni: str | None` - SNI sent to server
- `alpn: bytes | None` - Negotiated protocol
- `cipher: str | None`
- `certificate_list: Sequence[Cert]` - Server cert chain

**TLS Certificate Info** (`Cert` object):
- `subject: dict` - Subject DN (CN, O, OU, etc.)
- `issuer: dict` - Issuer DN
- `serial: int` - Serial number
- `notbefore / notafter: datetime` - Validity window
- `altnames: list[str]` - Subject Alternative Names

---

## 7. Flow Filtering (mitmproxy.flowfilter)

### Programmatic API
```python
from mitmproxy import flowfilter

# Compile filter
flt = flowfilter.parse("~d example.com & ~m POST")

# Test flow against filter
if flowfilter.match(flt, flow):
    # Flow matches
    pass
```

### Filter Syntax
| Filter | Matches |
|--------|---------|
| `~q` | Requests |
| `~s` | Responses |
| `~d <regex>` | Domain |
| `~m <regex>` | Method |
| `~u <regex>` | URL |
| `~c <code>` | Status code |
| `~h <regex>` | Any header (name: value) |
| `~hq <regex>` | Request header |
| `~hs <regex>` | Response header |
| `~b <regex>` | Any body |
| `~bq <regex>` | Request body |
| `~bs <regex>` | Response body |
| `~t <regex>` | Content-Type |
| `~a` | Assets (js, css, images) |
| `~e` | Errors |
| `!<filter>` | NOT |
| `<f> & <f>` | AND |
| `<f> \| <f>` | OR |
| `(<f>)` | Grouping |

---

## 8. Addon Event Hooks

### HTTP Hooks (most relevant)
- `request(flow: HTTPFlow)` - Full request received
- `response(flow: HTTPFlow)` - Full response received
- `requestheaders(flow: HTTPFlow)` - Request headers received (can set `stream`)
- `responseheaders(flow: HTTPFlow)` - Response headers received (can set `stream`)
- `http_connect(flow: HTTPFlow)` - CONNECT request received

### Connection Lifecycle
- `client_connected(client)` / `client_disconnected(client)`
- `server_connect(server)` / `server_connected(server)` / `server_disconnected(server)`

### TLS Hooks
- `tls_clienthello(data: TlsData)` - ClientHello received
- `tls_established(data: TlsData)` - TLS handshake completed

### WebSocket Hooks
- `websocket_message(flow: HTTPFlow)` - WebSocket message received
- `websocket_start(flow)` / `websocket_end(flow)` / `websocket_error(flow)`

### Addon Lifecycle
- `load(loader: Loader)` - Register options/commands
- `configure(updated: set[str])` - Options changed
- `running()` - mitmproxy is running
- `done()` - Shutting down

---

## 9. Streaming API

Set in `requestheaders` or `responseheaders` hook (before body received):
```python
def requestheaders(flow):
    flow.request.stream = True  # Simple passthrough

    # Or with transformation
    def transform(chunk: bytes) -> bytes:
        return chunk.upper()
    flow.request.stream = transform
```

Option-based: `--set stream_large_bodies=10m`

**Limitations**: Streamed content not accessible in `request`/`response` hooks. Headers still fully buffered.

---

## 10. Replay Capabilities

### Client Replay (CLI)
```bash
mitmdump -C replay.mitm                          # Replay all
mitmdump --client-replay-concurrency 5 -C replay.mitm  # Concurrent
```

### Server Replay (mock server)
```bash
mitmdump -S replay.mitm                    # Match by URL and method
mitmdump --server-replay-refresh -S replay.mitm  # Update timestamps
```

---

## 11. Built-in Features Worth Knowing

| Feature | Flag | Purpose |
|---------|------|---------|
| Anticache | `--anticache` | Remove if-none-match, if-modified-since — forces full responses |
| Sticky cookies | `--stickycookie "~d example.com"` | Auto-replay cookies from matching responses |
| Sticky auth | `--stickyauth "~d example.com"` | Auto-replay auth headers |
| Map local | `--map-local "\|pattern\|/local/path"` | Serve local files instead of remote |
| Map remote | `--map-remote "\|pattern\|replacement"` | Redirect requests to different server |
| Modify body | `--modify-body "/~q/search/replace"` | Replace content on the fly |
| Modify headers | `--modify-headers "/~q/Header/value"` | Replace headers on the fly |
| Blocklist | `--block-list ":~d ads.com:404"` | Block requests, return status code |

---

## 12. Proxy Modes Reference

| Mode | Command | Use Case |
|------|---------|----------|
| Regular | `mitmproxy` | Explicit proxy, client configures proxy settings |
| Reverse | `--mode reverse:https://target.com` | Sit in front of target server |
| Transparent | `--mode transparent` | Network-layer redirection, no client config |
| Local | `--mode local:curl` | Per-process capture on same host |
| WireGuard | `--mode wireguard` | VPN-based capture, no cert install needed |
| Upstream | `--mode upstream:http://proxy:8080` | Chain through another proxy |
| SOCKS5 | `--mode socks5` | Act as SOCKS5 proxy |

---

## 13. Corrections & Additions from API Reference

> Cross-referenced from `.claude/docs/mitmproxy/api/*.md` — fills gaps in the original research.

### Tier 1: Use Now (Recon Tools / Fingerprinting)

#### Request — Additional Properties & Methods

| Property/Method | Type/Signature | Why It Matters |
|-----------------|---------------|----------------|
| `path_components` | `tuple[str, ...]` | URL path segments as unquoted strings — useful for endpoint pattern extraction without manual splitting |
| `first_line_format` | `str` ("authority", "absolute", "relative") | Distinguishes CONNECT tunnels from regular requests |
| `anticache()` | `-> None` | Removes `If-None-Match`, `If-Modified-Since` — forces full responses during fingerprinting (same as `--anticache` flag but per-request) |
| `anticomp()` | `-> None` | Sets `Accept-Encoding: identity` — forces uncompressed responses for easier body inspection |
| `constrain_encoding()` | `-> None` | Limits `Accept-Encoding` to encodings mitmproxy can decode — prevents garbled bodies |
| `multipart_form` | `MultiDictView[bytes, bytes]` | **Type correction**: keys and values are `bytes`, not `str` |

#### Response — Cookie Structure (Type Correction)

**Critical**: `response.cookies` returns `MultiDictView[str, tuple[str, MultiDict[str, str | None]]]`

Each cookie is a tuple of `(value, attributes)`, NOT a flat string:
```python
for name, (value, attrs) in flow.response.cookies.items(multi=True):
    print(f"{name}={value}")
    print(f"  Path={attrs.get('path')}, HttpOnly={attrs.get('httponly')}")
```

This means our recon tools can extract cookie attributes (Path, Domain, HttpOnly, Secure, SameSite) directly — no Set-Cookie header parsing needed.

#### Connection — Richer Fingerprinting Data

| Attribute | Type | What It Adds |
|-----------|------|-------------|
| `alpn_offers` | `Sequence[bytes]` | ALPN protocols from ClientHello — reveals client capabilities (h2, http/1.1) |
| `cipher_list` | `Sequence[str]` | Ciphers accepted by proxy — useful for TLS fingerprinting |
| `state` | `ConnectionState` enum (`CLOSED=0`, `CAN_READ=1`, `CAN_WRITE=2`, `OPEN=3`) | Connection lifecycle tracking |
| `sockname` | `(str, int) \| None` | Local IP/port tuple |
| `transport_protocol` | `Literal["tcp", "udp"]` | Default "tcp" |
| `timestamp_end` | `float \| None` | Connection close time |
| `timestamp_tls_setup` | `float \| None` | TLS handshake completion time — measures TLS overhead |
| `server.timestamp_tcp_setup` | `float \| None` | TCP ACK received — measures network latency |

#### MultiDict — Behavioral Details

- `get_all(key)` returns **empty list** if key not found (no KeyError)
- `add(key, value)` appends at the **END** (position guaranteed)
- `MultiDictView.copy()` creates a standalone `MultiDict` (detached from parent)
- `items(multi=True)` yields every individual header; `items(multi=False)` folds duplicates

### Tier 2: Good to Know (Future Extensions)

#### Flow Lifecycle — Backup/Revert Pattern

```python
flow.backup()          # Snapshot current state
flow.request.url = "..." # Modify
if flow.modified():    # Check if changed since backup
    flow.revert()      # Restore to snapshot
```

Also: `flow.killable` (bool property), `flow.kill()` raises `ControlException` if not killable, `await flow.wait_for_resume()` for async addon use.

#### TLS Event Hook Data

| Dataclass | Key Attributes | Use Case |
|-----------|---------------|----------|
| `ClientHelloData` | `client_hello: ClientHello`, `ignore_connection: bool`, `establish_server_tls_first: bool` | Set `ignore_connection=True` to skip interception; set `establish_server_tls_first=True` to inspect server cert before completing client handshake |
| `TlsData` | `conn: Connection`, `ssl_conn: SSL.Connection \| None`, `is_dtls: bool` | Access pyOpenSSL object for custom TLS handling |
| `ClientHello` | `extensions: list[tuple[int, bytes]]`, `raw_bytes(wrap_in_record=True)` | Raw TLS extension access for JA3/JA4 fingerprinting |

#### WebSocket — Updated API

- `WebSocketMessage.dropped: bool` — blocked from forwarding
- `WebSocketMessage.injected: bool` — artificially created
- `WebSocketMessage.drop()` — preferred method (replaces deprecated `kill()`)
- `WebSocketData.closed_by_client: bool | None` — three-state: True/False/None
- `WebSocketData.close_code: int | None` — RFC 6455 close code

#### Server Connection Hooks — Error Handling

- Setting `client.error` in `client_connected` hook terminates the connection
- Setting `data.server.error` in `server_connect` hook terminates the connection
- Every server connection gets **either** `server_connected` **or** `server_connect_error`, never both
