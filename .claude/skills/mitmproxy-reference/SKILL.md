---
name: mitmproxy-reference
description: mitmproxy and mitmdump documentation — proxy modes, addon development, event hooks, traffic capture, filtering, and replay. Use when working with HTTP interception, building capture addons, or debugging proxy behavior.
allowed-tools: Read, Grep, Glob
---

# mitmproxy Onboarding Guide: Research & Best Practices

This document serves as the primary onboarding guide for any developer joining the LLMitM v2 project. It provides a high-level map of the mitmproxy documentation, followed by a curated set of deep-dive research reports that are essential for understanding our architecture, design patterns, and implementation choices. Each report is summarized to explain its relevance and provide context for why it is required reading.

---

## mitmproxy Documentation Map

This section provides a comprehensive, hierarchically structured map of the mitmproxy documentation, based on the cloned source files. It is designed to serve as a top-level exploration guide for understanding how mitmproxy powers LLMitM v2's traffic interception layer.

- **[Concepts (Entry Point)](../../docs/mitmproxy/concepts/_index.md)**
  - **Core Architecture**
    - [How mitmproxy Works: MITM Mechanism](../../docs/mitmproxy/concepts/how-mitmproxy-works.md)
    - [Proxy Modes: Regular, Reverse, Transparent, WireGuard, Local](../../docs/mitmproxy/concepts/modes.md)
    - [Protocol Support: HTTP/1, HTTP/2, HTTP/3, WebSocket, TCP, UDP](../../docs/mitmproxy/concepts/protocols.md)
    - [Certificates: CA Generation, Pinning, mTLS](../../docs/mitmproxy/concepts/certificates.md)
  - **Configuration & Filtering**
    - [Options System: YAML Config, Runtime Control](../../docs/mitmproxy/concepts/options.md)
    - [Filter Expressions: URL, Header, Method, Status Code Matching](../../docs/mitmproxy/concepts/filters.md)
    - [Commands: Interactive Console, Key Bindings](../../docs/mitmproxy/concepts/commands.md)

- **[Addon Development (Entry Point)](../../docs/mitmproxy/addons/_index.md)**
  - **Building Addons**
    - [Addon Architecture: Event Hooks, Options, Commands](../../docs/mitmproxy/addons/overview.md)
    - [Event Hooks: `request`, `response`, Connection Lifecycle](../../docs/mitmproxy/addons/event-hooks.md)
    - [Custom Options: Typed Config, Validation](../../docs/mitmproxy/addons/options.md)
    - [Custom Commands: `@command.command`, Flow Arguments](../../docs/mitmproxy/addons/commands.md)
  - **Reference**
    - [Content Views: Pretty-Printing, Syntax Highlighting](../../docs/mitmproxy/addons/contentviews.md)
    - [API Changelog: Breaking Changes Across Versions](../../docs/mitmproxy/addons/api-changelog.md)

- **[Overview (Entry Point)](../../docs/mitmproxy/overview/_index.md)**
  - [Built-in Features: Replay, Anticache, Map Local/Remote, Streaming](../../docs/mitmproxy/overview/features.md)
  - [Installation: macOS, Linux, Windows, Docker, PyPI](../../docs/mitmproxy/overview/installation.md)
  - [Getting Started: First Launch, Browser Config](../../docs/mitmproxy/overview/getting-started.md)

- **[How-To Guides (Entry Point)](../../docs/mitmproxy/howto/_index.md)**
  - [Transparent Proxying: iptables, pf, Network-Layer Setup](../../docs/mitmproxy/howto/transparent.md)
  - [Ignoring Domains: `ignore_hosts`, Certificate Pinning Workarounds](../../docs/mitmproxy/howto/ignore-domains.md)

- **[Tutorials (Entry Point)](../../docs/mitmproxy/tutorials/_index.md)**
  - [Client Replay: Capture Once, Replay Forever](../../docs/mitmproxy/tutorials/client-replay.md)

- **[API Reference (Entry Point)](../../docs/mitmproxy/api/_index.md)**
  - **Core Traffic**: [mitmproxy.http](../../docs/mitmproxy/api/mitmproxy.http.md) (Headers, Request, Response, HTTPFlow), [mitmproxy.flow](../../docs/mitmproxy/api/mitmproxy.flow.md) (Flow base, serialization), [mitmproxy.connection](../../docs/mitmproxy/api/mitmproxy.connection.md) (Client, Server, TLS metadata)
  - **Data Structures**: [mitmproxy.coretypes.multidict](../../docs/mitmproxy/api/mitmproxy.coretypes.multidict.md) (MultiDict used by headers, cookies, query, forms)
  - **TLS/Certs**: [mitmproxy.tls](../../docs/mitmproxy/api/mitmproxy.tls.md) (ClientHello, TlsData), [mitmproxy.certs](../../docs/mitmproxy/api/mitmproxy.certs.md) (Cert parsing, CA generation)
  - **Protocols**: [dns](../../docs/mitmproxy/api/mitmproxy.dns.md), [tcp](../../docs/mitmproxy/api/mitmproxy.tcp.md), [udp](../../docs/mitmproxy/api/mitmproxy.udp.md), [websocket](../../docs/mitmproxy/api/mitmproxy.websocket.md)
  - **Proxy**: [mode_specs](../../docs/mitmproxy/api/mitmproxy.proxy.mode_specs.md), [context](../../docs/mitmproxy/api/mitmproxy.proxy.context.md), [server_hooks](../../docs/mitmproxy/api/mitmproxy.proxy.server_hooks.md)
  - **Addon System**: [addonmanager](../../docs/mitmproxy/api/mitmproxy.addonmanager.md), [contentviews](../../docs/mitmproxy/api/mitmproxy.contentviews.md)

---

## Curated Research Reports

### 1. Core Architecture

#### [How mitmproxy Works](../../docs/mitmproxy/concepts/how-mitmproxy-works.md)
Core MITM mechanism: explicit HTTP/HTTPS proxying, transparent proxying, SNI handling, upstream certificate sniffing. Foundational for troubleshooting fingerprinting and traffic capture phases.

#### [Proxy Modes](../../docs/mitmproxy/concepts/modes.md)
All proxy modes: regular, transparent, reverse, WireGuard, local capture. LLMitM v2 uses **regular proxy** (explicit) and **reverse proxy** (in front of target). See [API Research — Proxy Modes](../../docs/mitmproxy/api_research.md#12-proxy-modes-reference) for the full mode reference table.

#### [Protocol Support](../../docs/mitmproxy/concepts/protocols.md)
HTTP/1, HTTP/2, HTTP/3, WebSocket, DNS, TCP/TLS, UDP/DTLS. LLMitM v2 focuses on HTTP/HTTPS. WebSocket hooks exist for future extensions.

#### [Certificates](../../docs/mitmproxy/concepts/certificates.md)
CA certificate system for HTTPS interception. Certificate pinning bypass via `ignore_hosts` or Android unpinning tools.

### 2. Python API (Critical for LLMitM v2)

> **Full API reference**: [api/_index.md](../../docs/mitmproxy/api/_index.md) — clean markdown docs for all 16 modules
> **Architecture insights**: [api_research.md](../../docs/mitmproxy/api_research.md) — FlowReader patterns, bounded tool design, codebase integration notes

#### FlowReader — The Key Insight

**The `.mitm` file IS the structured format.** `FlowReader` (`mitmproxy.io`) is a deserializer that yields fully hydrated Python objects — no subprocess, no text parsing, no truncation:

```python
from mitmproxy.io import FlowReader
with open("capture.mitm", "rb") as f:
    for flow in FlowReader(f).stream():
        flow.request.method       # "POST"
        flow.request.pretty_url   # "http://localhost:3000/rest/user/login"
        flow.request.json()       # {"email": "admin@juice-sh.op", "password": "admin123"}
        flow.request.cookies      # MultiDict of cookies
        flow.response.status_code # 200
        flow.response.json()      # {"authentication": {"token": "eyJ..."}}
        flow.response.cookies     # Set-Cookie values parsed
        flow.response.headers     # case-insensitive multidict
```

The CLI command `mitmdump -nr capture.mitm --flow-detail 3` is literally `FlowReader` -> format as text -> print to stdout. Shelling out to mitmdump gives a **lossy text representation** of data that's already structured.

#### HTTPFlow Object — What's Available

Every flow captured by mitmproxy gives you (full signatures in [mitmproxy.http](../../docs/mitmproxy/api/mitmproxy.http.md)):

| Category | Attributes |
|----------|-----------|
| **Request basics** | `method`, `url`, `pretty_url`, `scheme`, `host`, `port`, `path`, `http_version` |
| **Request data** | `headers` ([Headers](../../docs/mitmproxy/api/mitmproxy.http.md#headers) — case-insensitive [MultiDict](../../docs/mitmproxy/api/mitmproxy.coretypes.multidict.md)), `content` (decompressed bytes), `text`, `json()`, `cookies`, `query`, `urlencoded_form`, `multipart_form` |
| **Response basics** | `status_code`, `reason`, `http_version` |
| **Response data** | `headers`, `content`, `text`, `json()`, `cookies` |
| **Connection/TLS** | [Client](../../docs/mitmproxy/api/mitmproxy.connection.md#client)/[Server](../../docs/mitmproxy/api/mitmproxy.connection.md#server): `sni`, `tls_version`, `alpn`, `cipher`, `certificate_list` ([Cert](../../docs/mitmproxy/api/mitmproxy.certs.md) objects with subject, issuer, SANs) |
| **Flow lifecycle** | [Flow](../../docs/mitmproxy/api/mitmproxy.flow.md) base: `id` (UUID), `timestamp_created`, `is_replay`, `error`, `metadata` (arbitrary dict), `get_state()`/`set_state()`, `copy()`, `kill()` |

#### Programmatic Flow Filtering

```python
from mitmproxy import flowfilter
flt = flowfilter.parse("~d example.com & ~m POST")
if flowfilter.match(flt, flow):
    # Flow matches
```

Same filter syntax as CLI (`~u`, `~m`, `~c`, `~h`, `~b`, `~t`, `~d`, `&`, `|`, `!`) but compiled and evaluated in Python. See [api_research.md §7](../../docs/mitmproxy/api_research.md#7-flow-filtering-mitmproxyflowfilter) for the full filter table.

#### Useful Utilities

| Utility | What It Does |
|---------|-------------|
| `flow.response.refresh()` | Update date/expires/cookie timestamps for replay freshness |
| `Response.make(status_code, content, headers)` | Factory for mock responses ([mitmproxy.http](../../docs/mitmproxy/api/mitmproxy.http.md#response)) |
| `flow.get_state()` / `set_state()` | Serialize flow to/from dict ([mitmproxy.flow](../../docs/mitmproxy/api/mitmproxy.flow.md)) |
| `flow.copy()` | Deep copy with `live=False` |
| `FlowWriter(fo).add(flow)` | Write flows to `.mitm` binary format |
| `FilteredFlowWriter(fo, flt)` | Write only matching flows |
| `read_flows_from_paths(paths)` | Bulk read from multiple files |

### 3. Addon Development

#### [Addon Architecture Overview](../../docs/mitmproxy/addons/overview.md)
Class-based addons respond to event hooks, define options, expose commands. For LLMitM v2, addons are the natural way to implement live traffic capture and real-time fingerprinting without subprocess-based mitmdump invocations.

#### Event Hooks — What Fires When
| Hook | When | Use Case |
|------|------|----------|
| `request(flow)` | Full request received | Capture for fingerprinting |
| `response(flow)` | Full response received | Tech stack detection, token extraction |
| `requestheaders(flow)` | Headers only, before body | Set `flow.request.stream = True` for large files |
| `responseheaders(flow)` | Headers only, before body | Streaming decisions |
| `tls_clienthello(data)` | TLS ClientHello | SNI, cipher suite analysis |
| `websocket_message(flow)` | WebSocket message | Future: non-HTTP protocol testing |

See [API Research — Event Hooks](../../docs/mitmproxy/api_research.md#8-addon-event-hooks) for the complete hook list.

#### [Custom Options](../../docs/mitmproxy/addons/options.md) & [Custom Commands](../../docs/mitmproxy/addons/commands.md)
Addons can define typed options (str, int, bool, sequences) and expose commands that accept flows, paths, and other typed arguments. Relevant for future: `"compile ActionGraph from current flows"` or `"execute stored graph for domain X"`.

### 4. Configuration & Filtering

#### [Options System](../../docs/mitmproxy/concepts/options.md)
Global options via `~/.mitmproxy/config.yaml` and `--set`. Key options: `ignore_hosts`, `tcp_hosts`, `mode`, `anticache`, `stickycookie`, `stickyauth`.

#### [Filter Expressions](../../docs/mitmproxy/concepts/filters.md)
Flow matching language: `~u /api & ~m POST & ~c 200`. Works both in CLI and programmatically via `flowfilter.parse()`.

#### Built-in Features Worth Knowing
| Feature | Flag | Why It Matters |
|---------|------|----------------|
| **Anticache** | `--anticache` | Forces full responses during fingerprinting |
| **Sticky cookies** | `--stickycookie "~d target"` | Auto-replay session cookies (our `ExecutionContext.cookies` does this manually) |
| **Sticky auth** | `--stickyauth "~d target"` | Auto-replay auth headers |
| **Client replay** | `-C replay.mitm` | Replay captured requests against live server |
| **Streaming** | `--stream_large_bodies=10m` | Forward large bodies without buffering |

### 5. Operations & Deployment

#### [Transparent Proxying](../../docs/mitmproxy/howto/transparent.md)
Network-layer setup via iptables (Linux), pf (macOS). Captures traffic from proxy-oblivious applications.

#### [Ignoring Domains](../../docs/mitmproxy/howto/ignore-domains.md)
`ignore_hosts` option exempts traffic from interception. Filter out CDNs, analytics, etc.

### 6. API Compatibility

#### [API Changelog](../../docs/mitmproxy/addons/api-changelog.md)
Key breaking changes: mitmproxy 9+ uses Python `logging` (not custom); mitmproxy 7+ revised connection events (`.client_conn` -> `.peername`).

### 7. Tutorials

#### [Client Replay Tutorial](../../docs/mitmproxy/tutorials/client-replay.md)
Capture and replay HTTP login sequences: `mitmdump -w` (record) -> `mitmdump -C` (replay). Validates the core LLMitM v2 thesis: capture once, replay deterministically forever.
