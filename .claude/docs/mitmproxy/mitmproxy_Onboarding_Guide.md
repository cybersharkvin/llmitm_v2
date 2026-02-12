# mitmproxy Onboarding Guide: Research & Best Practices

This document serves as the primary onboarding guide for any developer joining the LLMitM v2 project. It provides a high-level map of the mitmproxy documentation, followed by a curated set of deep-dive research reports that are essential for understanding our architecture, design patterns, and implementation choices. Each report is summarized to explain its relevance and provide context for why it is required reading.

---

## mitmproxy Documentation Map

This section provides a comprehensive, hierarchically structured map of the mitmproxy documentation, based on the cloned source files. It is designed to serve as a top-level exploration guide for understanding how mitmproxy powers LLMitM v2's traffic interception layer.

- **[Concepts (Entry Point)](./concepts/_index.md)**
  - **Core Architecture**
    - [How mitmproxy Works: MITM Mechanism](./concepts/how-mitmproxy-works.md)
    - [Proxy Modes: Regular, Reverse, Transparent, WireGuard, Local](./concepts/modes.md)
    - [Protocol Support: HTTP/1, HTTP/2, HTTP/3, WebSocket, TCP, UDP](./concepts/protocols.md)
    - [Certificates: CA Generation, Pinning, mTLS](./concepts/certificates.md)
  - **Configuration & Filtering**
    - [Options System: YAML Config, Runtime Control](./concepts/options.md)
    - [Filter Expressions: URL, Header, Method, Status Code Matching](./concepts/filters.md)
    - [Commands: Interactive Console, Key Bindings](./concepts/commands.md)

- **[Addon Development (Entry Point)](./addons/_index.md)**
  - **Building Addons**
    - [Addon Architecture: Event Hooks, Options, Commands](./addons/overview.md)
    - [Event Hooks: `request`, `response`, Connection Lifecycle](./addons/event-hooks.md)
    - [Custom Options: Typed Config, Validation](./addons/options.md)
    - [Custom Commands: `@command.command`, Flow Arguments](./addons/commands.md)
  - **Reference**
    - [Content Views: Pretty-Printing, Syntax Highlighting](./addons/contentviews.md)
    - [API Changelog: Breaking Changes Across Versions](./addons/api-changelog.md)

- **[Overview (Entry Point)](./overview/_index.md)**
  - [Built-in Features: Replay, Anticache, Map Local/Remote, Streaming](./overview/features.md)
  - [Installation: macOS, Linux, Windows, Docker, PyPI](./overview/installation.md)
  - [Getting Started: First Launch, Browser Config](./overview/getting-started.md)

- **[How-To Guides (Entry Point)](./howto/_index.md)**
  - [Transparent Proxying: iptables, pf, Network-Layer Setup](./howto/transparent.md)
  - [Ignoring Domains: `ignore_hosts`, Certificate Pinning Workarounds](./howto/ignore-domains.md)

- **[Tutorials (Entry Point)](./tutorials/_index.md)**
  - [Client Replay: Capture Once, Replay Forever](./tutorials/client-replay.md)

- **[API Reference (Entry Point)](./api/_index.md)**
  - _Note: API docs reference auto-generated HTML from mitmproxy source. Key modules: `mitmproxy.http`, `mitmproxy.flow`, `mitmproxy.connection`, `mitmproxy.tls`._

---

## Curated Research Reports

### 1. Core Architecture

#### [How mitmproxy Works](./concepts/how-mitmproxy-works.md)
This doc explains mitmproxy's core MITM mechanism, which is foundational for LLMitM v2's traffic interception. It covers how mitmproxy handles both explicit HTTP/HTTPS proxying and transparent proxying, including SNI handling and upstream certificate sniffing. Understanding these internals is critical for troubleshooting fingerprinting and traffic capture phases.

#### [Proxy Modes](./concepts/modes.md)
This doc catalogs all mitmproxy proxy modes (regular, transparent, reverse, WireGuard, local capture). For LLMitM v2, the most relevant modes are **regular proxy** (explicit client configuration) and **reverse proxy** (putting mitmproxy in front of a target server). These modes determine how traffic is captured for fingerprinting and ActionGraph compilation.

#### [Protocol Support](./concepts/protocols.md)
This doc lists protocol support and limitations in mitmproxy (HTTP/1, HTTP/2, HTTP/3, WebSocket, DNS, TCP/TLS, UDP/DTLS). LLMitM v2 currently focuses on HTTP/HTTPS, but understanding WebSocket and generic TCP/TLS proxy capabilities is useful for future extensions to capture non-HTTP vulnerability patterns.

#### [Certificates](./concepts/certificates.md)
This doc details mitmproxy's CA certificate system, which is essential for LLMitM v2 to intercept HTTPS traffic. It covers certificate installation on clients, upstream certificate sniffing, certificate pinning challenges, and custom CA/server certificate usage. Certificate pinning is a major blocker for interception and can be addressed using `ignore_hosts` or Android unpinning tools.

### 2. Addon Development

#### [Addon Architecture Overview](./addons/overview.md)
This doc introduces mitmproxy's addon architecture, which is the primary extension mechanism. Addons respond to event hooks, define options, and expose commands. For LLMitM v2, addons are the natural way to implement live traffic capture, real-time fingerprinting, and ActionGraph execution hooks without subprocess-based mitmdump invocations.

#### [Event Hooks](./addons/event-hooks.md)
This doc lists all available event hooks in mitmproxy's addon system (e.g., `http_connect`, `request`, `response`, `server_connected`). For LLMitM v2, the most critical hooks are `request` (capture outgoing requests for fingerprinting) and `response` (capture responses for tech stack detection). These hooks receive `Flow` objects that can be modified in-place.

#### [Custom Addon Options](./addons/options.md)
This doc explains how addons define custom options that integrate with mitmproxy's global options store. Options are typed (str, int, bool, sequences) and can be validated in the `configure` event. For LLMitM v2, custom options could include Neo4j connection strings, model IDs, similarity thresholds, and target URLs.

#### [Custom Addon Commands](./addons/commands.md)
This doc shows how addons expose custom commands that users can invoke interactively or bind to keys. Commands are typed and can accept flows, paths, and other arguments. For LLMitM v2, commands like "compile ActionGraph from current flows" or "execute stored graph for domain X" would be powerful workflow accelerators.

### 3. Configuration & Filtering

#### [Options System](./concepts/options.md)
This doc explains mitmproxy's global options system, which controls runtime behavior via `~/.mitmproxy/config.yaml` and `--set` CLI flags. For LLMitM v2, key options include `ignore_hosts`, `tcp_hosts`, `mode`, and `anticache`. Addons can define custom options, which is relevant for extending the system with new fingerprinting or execution capabilities.

#### [Filter Expressions](./concepts/filters.md)
This doc describes mitmproxy's filter expression language for matching flows based on URL, headers, methods, status codes, etc. For LLMitM v2, filters are useful for isolating target traffic during fingerprinting (e.g., `~d example.com & ~m GET`) and for selective ActionGraph execution.

#### [Commands Framework](./concepts/commands.md)
This doc explains mitmproxy's command system, which allows users to interact with addons via CLI or interactive console. Commands can take flows as arguments using filter specs. For LLMitM v2, custom commands could expose operations like "replay ActionGraph for flow X" or "re-fingerprint target Y".

### 4. Operations & Deployment

#### [Built-in Features](./overview/features.md)
This doc catalogs mitmproxy's built-in features (anticache, blocklist, client/server replay, map local/remote, modify body/headers, streaming). For LLMitM v2, **client replay** is directly relevant for replaying captured requests during ActionGraph execution, and **anticache** ensures complete responses during fingerprinting.

#### [Transparent Proxying](./howto/transparent.md)
This doc provides OS-specific instructions for setting up transparent proxying via iptables (Linux), pf (macOS/OpenBSD), and RemoteAccess (Windows). For LLMitM v2, transparent mode is useful for capturing traffic from proxy-oblivious applications without client configuration. Requires network-layer routing and IP forwarding.

#### [Ignoring Domains](./howto/ignore-domains.md)
This doc explains the `ignore_hosts` option for exempting traffic from mitmproxy interception. For LLMitM v2, `ignore_hosts` can filter out irrelevant traffic during fingerprinting or exclude known non-vulnerable endpoints from ActionGraph execution.

### 5. API Compatibility

#### [API Changelog](./addons/api-changelog.md)
This doc tracks breaking API changes across mitmproxy versions. Most relevant for LLMitM v2: mitmproxy 9+ replaced homegrown logging with Python's `logging` module, and mitmproxy 7+ revised connection events (`.client_conn` → `.peername`). Knowing these changes prevents compatibility issues when upgrading mitmproxy.

### 6. Tutorials

#### [Client Replay Tutorial](./tutorials/client-replay.md)
This tutorial demonstrates a workflow for capturing and replaying HTTP login sequences using mitmdump. For LLMitM v2, this validates the practicality of ActionGraph compilation and warm-start execution: capture once, replay deterministically forever. The tutorial shows real-world value — automating tedious authentication flows with `mitmdump -w` (record) and `mitmdump -C` (replay).
