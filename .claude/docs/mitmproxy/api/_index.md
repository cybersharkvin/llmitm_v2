# mitmproxy API Reference

Clean markdown extractions of the mitmproxy Python API from [docs.mitmproxy.org/stable/api](https://docs.mitmproxy.org/stable/api/). These are the classes and methods available when working with mitmproxy programmatically — via `FlowReader` for offline `.mitm` analysis, via addon event hooks for live interception, or via direct object construction in tests. Each file covers one module's public API surface: signatures, type annotations, and docstrings (no source code).

---

## Core Traffic Objects

- **[mitmproxy.http](./mitmproxy.http.md)** — `Headers`, `Request`, `Response`, `HTTPFlow`. The primary API for inspecting and modifying HTTP traffic — URL components, JSON bodies, cookies, form data, and header manipulation.

- **[mitmproxy.flow](./mitmproxy.flow.md)** — `Flow` base class and `Error`. Flow lifecycle management, serialization (`get_state`/`set_state`), control (kill, intercept, resume), and metadata storage.

- **[mitmproxy.connection](./mitmproxy.connection.md)** — `Client`, `Server`, `Connection` base class, `ConnectionState`. Connection metadata including TLS version, SNI, ALPN, cipher, certificate chain, and peer addresses.

- **[mitmproxy.coretypes.multidict](./mitmproxy.coretypes.multidict.md)** — `MultiDict` and `MultiDictView`. Dictionary-like containers supporting multiple values per key, used by `Headers`, `cookies`, `query`, and form data.

## TLS & Certificates

- **[mitmproxy.tls](./mitmproxy.tls.md)** — `ClientHello`, `ClientHelloData`, `TlsData`. TLS handshake event data for SNI extraction, cipher suite analysis, and custom certificate injection.

- **[mitmproxy.certs](./mitmproxy.certs.md)** — `Cert`, `CertStore`, `CertStoreEntry`. Certificate parsing (subject, issuer, SANs, expiration), CA generation, and on-the-fly certificate creation for MITM interception.

## Protocol-Specific Flows

- **[mitmproxy.dns](./mitmproxy.dns.md)** — `DNSFlow`, `DNSMessage`, `Question`, `ResourceRecord`. DNS protocol handling with factory methods for creating A, AAAA, CNAME records.

- **[mitmproxy.tcp](./mitmproxy.tcp.md)** — `TCPFlow`, `TCPMessage`. Raw TCP session capture with individual message units and serialization support.

- **[mitmproxy.udp](./mitmproxy.udp.md)** — `UDPFlow`, `UDPMessage`. UDP datagram capture, mirroring TCP's structure.

- **[mitmproxy.websocket](./mitmproxy.websocket.md)** — `WebSocketMessage`, `WebSocketData`. WebSocket message capture with text/binary support and per-message metadata.

## Proxy Infrastructure

- **[mitmproxy.proxy.mode_specs](./mitmproxy.proxy.mode_specs.md)** — `ProxyMode` base class and 9 concrete modes: `RegularMode`, `TransparentMode`, `ReverseMode`, `UpstreamMode`, `Socks5Mode`, `WireGuardMode`, `LocalMode`, etc.

- **[mitmproxy.proxy.context](./mitmproxy.proxy.context.md)** — `Context` class holding client/server connections, options, and protocol layers for a single proxy session.

- **[mitmproxy.proxy.server_hooks](./mitmproxy.proxy.server_hooks.md)** — Connection lifecycle hooks: `ClientConnectedHook`, `ClientDisconnectedHook`, `ServerConnectHook`, `ServerConnectedHook`, `ServerDisconnectedHook`, `ServerConnectErrorHook`.

- **[mitmproxy.net.server_spec](./mitmproxy.net.server_spec.md)** — `ServerSpec` type alias and `parse()` function for parsing server addresses like `https://example.com:443`.

## Addon System

- **[mitmproxy.addonmanager](./mitmproxy.addonmanager.md)** — `Loader`, `AddonManager`, `LoadHook`. Addon registration, option/command declaration, and event dispatching lifecycle.

- **[mitmproxy.contentviews](./mitmproxy.contentviews.md)** — `Contentview` protocol and `InteractiveContentview`. Content formatting, decoding, and syntax highlighting for flow inspection.
