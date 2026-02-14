# mitmproxy.net.server_spec

## Overview

"Server specs are used to describe an upstream proxy or server."

## Type Definitions

### ServerSpec

```python
ServerSpec = tuple[
    Literal["http", "https", "http3", "tls", "dtls", "tcp", "udp", "dns", "quic"],
    tuple[str, int],
]
```

A tuple representing a server specification, containing a protocol scheme and a host-port pair.

## Module-Level Variables

### server_spec_re

```python
server_spec_re: re.Pattern
```

Regular expression pattern for parsing server specifications. Matches optional scheme, hostname (DNS, IPv4, or IPv6), and optional port.

## Functions

### parse()

```python
@cache
def parse(server_spec: str, default_scheme: str) -> ServerSpec
```

**Parameters:**
- `server_spec` (str): Server specification string to parse
- `default_scheme` (str): Default scheme to apply if none specified

**Returns:** `ServerSpec` - Parsed server specification tuple

**Raises:** `ValueError` - If the server specification or scheme is invalid, hostname is invalid, port is missing (for schemes requiring it), or port is invalid

**Description:**

Parses server mode specifications. Accepts formats including:
- `http://example.com/`
- `example.org`
- `example.com:443`

Default ports are inferred for: http (80), https (443), quic (443), http3 (443), and dns (53). Other schemes require explicit port specification.
