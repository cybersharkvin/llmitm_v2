# mitmproxy.proxy.context

## Class: Context

The context object provided to each protocol layer in the proxy core.

### Attributes

**`client: mitmproxy.connection.Client`**

The client connection.

**`server: mitmproxy.connection.Server`**

The server connection. Always set for practical reasons, even when no server connection exists yet. In that case, the server address is `None`.

**`options: Options`**

Provides access to options for proxy layers. Not intended for addon use; addons should use `mitmproxy.ctx.options` instead.

**`layers: list[mitmproxy.proxy.layer.Layer]`**

The protocol layer stack.

### Methods

**`__init__(client: connection.Client, options: Options) -> None`**

Initializes a Context instance with a client connection and options. Creates a Server instance with `None` address and initializes an empty layers list.

**`fork() -> Context`**

Creates a shallow copy of the current context, preserving client, options, server, and a copy of the layers list.

**`__repr__(self)`**

Returns a formatted string representation of the Context, displaying client, server, and layers information.
