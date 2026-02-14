# mitmproxy.certs

## Classes

### Cert

Representation of a (TLS) certificate.

#### Constructor
```python
Cert(cert: x509.Certificate)
```

#### Class Methods
```python
@classmethod
from_pem(cls, data: bytes) -> Cert
```
Load certificate from PEM-encoded data.

```python
@classmethod
from_pyopenssl(cls, x509: OpenSSL.crypto.X509) -> Cert
```
Create from PyOpenSSL X509 object.

```python
@classmethod
from_state(cls, state) -> Cert
```
Deserialize certificate from state.

#### Instance Methods
```python
to_pem(self) -> bytes
```
Export certificate as PEM-encoded bytes.

```python
to_cryptography(self) -> x509.Certificate
```
Return underlying cryptography Certificate object.

```python
to_pyopenssl(self) -> OpenSSL.crypto.X509
```
*Deprecated. Use `to_cryptography()` instead.*

```python
public_key(self) -> CertificatePublicKeyTypes
```
Extract the public key.

```python
fingerprint(self) -> bytes
```
Compute SHA256 fingerprint.

```python
has_expired(self) -> bool
```
Check if certificate has expired.

```python
get_state(self) -> bytes
```
Serialize to state (PEM format).

```python
set_state(self, state: bytes) -> None
```
Restore from serialized state.

#### Properties
```python
issuer: list[tuple[str, str]]
```
Issuer distinguished name as key-value pairs.

```python
notbefore: datetime.datetime
```
Certificate validity start time (UTC).

```python
notafter: datetime.datetime
```
Certificate validity end time (UTC).

```python
subject: list[tuple[str, str]]
```
Subject distinguished name as key-value pairs.

```python
serial: int
```
Certificate serial number.

```python
is_ca: bool
```
Whether certificate is a CA certificate.

```python
keyinfo: tuple[str, int]
```
Key algorithm and size (e.g., `("RSA", 2048)`).

```python
cn: str | None
```
Common Name from subject.

```python
organization: str | None
```
Organization name from subject.

```python
altnames: x509.GeneralNames
```
"Get all SubjectAlternativeName DNS altnames."

```python
crl_distribution_points: list[str]
```
CRL distribution point URLs.

---

### CertStore

In-memory certificate storage and generation.

#### Constructor
```python
CertStore(
    default_privatekey: rsa.RSAPrivateKey,
    default_ca: Cert,
    default_chain_file: Path | None,
    default_crl: bytes,
    dhparams: DHParams
)
```

#### Class Methods
```python
@classmethod
from_store(
    cls,
    path: Path | str,
    basename: str,
    key_size: int,
    passphrase: bytes | None = None
) -> CertStore
```
Load certificate store from filesystem path.

```python
@classmethod
from_files(
    cls,
    ca_file: Path,
    dhparam_file: Path,
    passphrase: bytes | None = None
) -> CertStore
```
Load from specific CA and DH parameter files.

```python
@staticmethod
create_store(
    path: Path,
    basename: str,
    key_size: int,
    organization: str | None = None,
    cn: str | None = None
) -> None
```
Generate new CA certificate store.

```python
@staticmethod
load_dhparam(path: Path) -> DHParams
```
Load Diffie-Hellman parameters from file.

#### Instance Methods
```python
add_cert(self, entry: CertStoreEntry, *names: str) -> None
```
Register certificate with optional domain names.

```python
add_cert_file(
    self,
    spec: str,
    path: Path,
    passphrase: bytes | None = None
) -> None
```
Load certificate from file and register.

```python
get_cert(
    self,
    commonname: str | None,
    sans: Iterable[x509.GeneralName],
    organization: str | None = None,
    crl_url: str | None = None
) -> CertStoreEntry
```
Retrieve or generate certificate. Performs wildcard matching against stored certificates.

```python
expire(self, entry: CertStoreEntry) -> None
```
Mark certificate for eviction (capacity: 100 entries).

```python
@staticmethod
asterisk_forms(dn: str | x509.GeneralName) -> list[str]
```
Generate wildcard domain variants (e.g., `www.example.com` → `[www.example.com, *.example.com, *.com]`).

#### Attributes
```python
STORE_CAP: int = 100
certs: dict[TCertId, CertStoreEntry]
dhparams: DHParams
default_privatekey: rsa.RSAPrivateKey
default_ca: Cert
default_chain_certs: list[Cert]
expire_queue: list[CertStoreEntry]
```

---

### CertStoreEntry

```python
@dataclass(frozen=True)
class CertStoreEntry:
    cert: Cert
    privatekey: rsa.RSAPrivateKey
    chain_file: Path | None
    chain_certs: list[Cert]
```

Certificate with associated private key and chain.

---

## Functions

```python
def create_ca(
    organization: str,
    cn: str,
    key_size: int
) -> tuple[rsa.RSAPrivateKeyWithSerialization, x509.Certificate]
```
Generate a new CA certificate and private key.

```python
def dummy_cert(
    privkey: rsa.RSAPrivateKey,
    cacert: x509.Certificate,
    commonname: str | None,
    sans: Iterable[x509.GeneralName],
    organization: str | None = None,
    crl_url: str | None = None
) -> Cert
```
Generate a leaf certificate signed by CA.

```python
def dummy_crl(
    privkey: rsa.RSAPrivateKey,
    cacert: x509.Certificate
) -> bytes
```
Generate empty CRL signed with CA key (DER-encoded).

```python
def load_pem_private_key(
    data: bytes,
    password: bytes | None
) -> rsa.RSAPrivateKey
```
Load PEM private key, gracefully falling back if unencrypted.

---

## Type Aliases

```python
TCustomCertId = str
TGeneratedCertId = tuple[Optional[str], x509.GeneralNames]
TCertId = Union[TCustomCertId, TGeneratedCertId]
DHParams = NewType("DHParams", bytes)
```

---

## Constants

```python
CA_EXPIRY: datetime.timedelta = timedelta(days=3650)
CERT_EXPIRY: datetime.timedelta = timedelta(days=365)
CRL_EXPIRY: datetime.timedelta = timedelta(days=7)
DEFAULT_DHPARAM: bytes
```
