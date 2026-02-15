# mitmproxy.dns

## Classes

### Question

A DNS question representation.

```python
@dataclass
class Question(serializable.SerializableDataclass):
    name: str
    type: int
    class_: int
```

**Methods:**

- `__str__() -> str` — Returns the question name
- `to_json() -> dict` — Converts question to JSON for mitmweb
- `from_json(data: dict[str, str]) -> Self` — Reconstructs question from JSON

---

### ResourceRecord

A DNS resource record representation.

```python
@dataclass
class ResourceRecord(serializable.SerializableDataclass):
    DEFAULT_TTL: ClassVar[int] = 60

    name: str
    type: int
    class_: int
    ttl: int
    data: bytes
```

**Properties:**

- `text: str` — Get/set record data as UTF-8 text
- `ipv4_address: IPv4Address` — Get/set as IPv4 address
- `ipv6_address: IPv6Address` — Get/set as IPv6 address
- `domain_name: str` — Get/set as domain name
- `https_alpn: tuple[bytes, ...] | None` — Get/set ALPN from HTTPS records
- `https_ech: str | None` — Get/set ECH (base64-encoded) from HTTPS records

**Methods:**

- `__str__() -> str` — Returns string representation of record data
- `to_json() -> dict[str, str | int | HTTPSRecordJSON]` — Converts to JSON
- `from_json(data: dict[str, Any]) -> Self` — Reconstructs from JSON
- `A(name: str, ip: IPv4Address, *, ttl: int = DEFAULT_TTL) -> ResourceRecord` — Creates IPv4 record
- `AAAA(name: str, ip: IPv6Address, *, ttl: int = DEFAULT_TTL) -> ResourceRecord` — Creates IPv6 record
- `CNAME(alias: str, canonical: str, *, ttl: int = DEFAULT_TTL) -> ResourceRecord` — Creates canonical name record
- `PTR(inaddr: str, ptr: str, *, ttl: int = DEFAULT_TTL) -> ResourceRecord` — Creates pointer record
- `TXT(name: str, text: str, *, ttl: int = DEFAULT_TTL) -> ResourceRecord` — Creates text record
- `HTTPS(name: str, record: HTTPSRecord, ttl: int = DEFAULT_TTL) -> ResourceRecord` — Creates HTTPS record

---

### DNSMessage

A complete DNS protocol message.

```python
@dataclass
class DNSMessage(serializable.SerializableDataclass):
    id: int
    query: bool
    op_code: int
    authoritative_answer: bool
    truncation: bool
    recursion_desired: bool
    recursion_available: bool
    reserved: int
    response_code: int
    questions: list[Question]
    answers: list[ResourceRecord]
    authorities: list[ResourceRecord]
    additionals: list[ResourceRecord]
    timestamp: float | None = None
```

**Field Descriptions:**

- `id` — "An identifier assigned by the program that generates any kind of query"
- `query` — "A field that specifies whether this message is a query"
- `op_code` — "A field that specifies kind of query in this message"
- `authoritative_answer` — "Specifies that the responding name server is an authority for the domain"
- `truncation` — "Specifies that this message was truncated due to length constraints"
- `recursion_desired` — "Directs the name server to pursue the query recursively"
- `recursion_available` — "Denotes whether recursive query support is available"
- `reserved` — "Reserved for future use. Must be zero in all queries and responses"
- `response_code` — "This field is set as part of responses"
- `timestamp` — "The time at which the message was sent or received"

**Properties:**

- `content: bytes` — Returns packed message bytes
- `question: Question | None` — Shorthand for single question (returns first if exactly one exists)
- `size: int` — Cumulative data size of all resource record sections

**Methods:**

- `__str__() -> str` — Returns string representation of all sections
- `fail(response_code: int) -> DNSMessage` — Creates error response
- `succeed(answers: list[ResourceRecord]) -> DNSMessage` — Creates successful response
- `unpack(buffer: bytes, timestamp: float | None = None) -> DNSMessage` — Converts buffer to DNS message
- `unpack_from(buffer: bytes | bytearray, offset: int, timestamp: float | None = None) -> tuple[int, DNSMessage]` — Unpacks from offset, returns length and message
- `packed: bytes` — Converts message to network bytes
- `to_json() -> dict` — Converts to JSON for mitmweb
- `from_json(data: Any) -> DNSMessage` — Reconstructs from JSON
- `copy() -> DNSMessage` — Creates copy with randomized ID

---

### DNSFlow

A DNS flow representing a single DNS query and optional response.

```python
class DNSFlow(flow.Flow):
    request: DNSMessage
    response: DNSMessage | None = None
```

**Attributes:**

- `request` — "The DNS request"
- `response` — "The DNS response"
- `type: ClassVar[str] = 'dns'` — The flow type identifier

**Methods:**

- `get_state() -> serializable.State` — Returns serializable state
- `set_state(state: serializable.State) -> None` — Restores from state
- `__repr__() -> str` — Returns string representation

**Inherited from Flow:** client_conn, server_conn, error, intercepted, marked, is_replay, live, timestamp_created, id, metadata, comment, copy, modified, backup, revert, killable, kill, intercept, wait_for_resume, resume, timestamp_start
