# mitmproxy.tls

## Classes

### ClientHello

Represents the initial TLS message sent by a client when establishing a secure connection.

#### Constructor

```python
ClientHello(raw_client_hello: bytes, dtls: bool = False)
```

Creates a TLS ClientHello object from raw bytes. The `dtls` parameter indicates whether to parse as DTLS format.

#### Methods

##### raw_bytes

```python
raw_bytes(wrap_in_record: bool = True) -> bytes
```

Returns the raw ClientHello bytes as transmitted on the wire. When `wrap_in_record` is True, wraps the message in a synthetic TLS record with format `0x160303 + len(chm) + 0x01 + len(ch)`, suitable for external tools. The synthetic record assumes TLS version `0x0303`. Note: DTLS format is not currently supported for this operation.

#### Properties

##### cipher_suites

```python
cipher_suites: list[int]
```

List of cipher suites advertised by the client as integer values.

##### sni

```python
sni: str | None
```

The Server Name Indication extension value indicating the target hostname, or None if absent or invalid.

##### alpn_protocols

```python
alpn_protocols: list[bytes]
```

Application-layer protocols offered via the ALPN TLS extension.

##### extensions

```python
extensions: list[tuple[int, bytes]]
```

Raw TLS extensions as tuples pairing extension type identifiers with their byte payloads.

---

### ClientHelloData

Event data structure for `tls_clienthello` event hooks.

```python
@dataclass
class ClientHelloData
```

#### Fields

- **context** (`context.Context`): Connection context information
- **client_hello** (`ClientHello`): Parsed TLS ClientHello message
- **ignore_connection** (`bool`, default=False): When True, prevents interception and forwards encrypted traffic unchanged
- **establish_server_tls_first** (`bool`, default=False): When True, delays client handshake to first establish server-side TLS, enabling certificate inspection before generating interception certificates

---

### TlsData

Event data structure for `tls_start_client`, `tls_start_server`, and `tls_handshake` event hooks.

```python
@dataclass
class TlsData
```

#### Fields

- **conn** (`connection.Connection`): The affected network connection
- **context** (`context.Context`): Connection context information
- **ssl_conn** (`SSL.Connection | None`, default=None): pyOpenSSL SSL.Connection object, populated by addons during `tls_start_*` hooks
- **is_dtls** (`bool`, default=False): Indicates whether this is a DTLS event
