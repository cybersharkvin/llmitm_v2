# mitmdump CLI Reference

## Overview

mitmdump is your primary tool for intercepting, analyzing, and replaying HTTP traffic.
All network operations happen through mitmdump commands via the `mitmdump` tool.

## Reading Captured Traffic

```bash
# Show all flows from a capture file with full request/response detail
mitmdump -nr capture.mitm --flow-detail 3

# Filter to specific paths
mitmdump -nr capture.mitm --flow-detail 3 -B '~u /api/'

# Filter by response code
mitmdump -nr capture.mitm --flow-detail 3 -B '~c 200'

# Filter by method
mitmdump -nr capture.mitm --flow-detail 3 -B '~m POST'

# Combine filters (AND)
mitmdump -nr capture.mitm --flow-detail 3 -B '~m GET & ~u /api/Users'

# Negate filters
mitmdump -nr capture.mitm --flow-detail 3 -B '!~c 304'
```

## Filter Expressions

| Filter | Meaning |
|--------|---------|
| `~u REGEX` | URL matches regex |
| `~m METHOD` | HTTP method matches |
| `~c CODE` | Response status code matches |
| `~h REGEX` | Header matches regex (request or response) |
| `~hq REGEX` | Request header matches |
| `~hs REGEX` | Response header matches |
| `~b REGEX` | Body matches regex |
| `~bq REGEX` | Request body matches |
| `~bs REGEX` | Response body matches |
| `~t CONTENT_TYPE` | Content-type matches |
| `~d DOMAIN` | Domain matches |
| `& / \|` | AND / OR |
| `!` | NOT |

## Live Capture (Reverse Proxy Mode)

```bash
# Start reverse proxy capturing to file
mitmdump -m reverse:http://target:3000 -w capture.mitm -p 8080

# With SSL stripping
mitmdump -m reverse:https://target:443 --ssl-insecure -w capture.mitm
```

## Replaying Traffic

```bash
# Replay captured requests against target
mitmdump -nc capture.mitm --replay-server capture.mitm

# Replay specific requests (filter first, replay filtered)
mitmdump -nr capture.mitm -B '~u /api/Users' -w filtered.mitm
mitmdump -nc filtered.mitm --replay-server filtered.mitm
```

## Modifying Requests (Scripting)

```bash
# Modify headers on replay
mitmdump -nr capture.mitm --modify-headers '/~q/Authorization/Bearer NEWTOKEN'

# Modify body content
mitmdump -nr capture.mitm --modify-body '/~q & ~u /api/login/{"email":"admin@test.com"}'

# Replace path segments
mitmdump -nr capture.mitm --map-remote '|/api/Users/1|/api/Users/2|'
```

## Flow Detail Levels

| Level | Shows |
|-------|-------|
| 0 | Nothing |
| 1 | One line per flow (method, URL, status) |
| 2 | Headers |
| 3 | Full request and response bodies |
| 4 | Hex dump |

## Common Patterns for Security Testing

### Extract all unique endpoints
```python
flows = await mitmdump("-nr capture.mitm --flow-detail 1")
# Parse output to find unique paths
```

### Check auth requirements
```python
# Request without auth
no_auth = await mitmdump("-nr capture.mitm --flow-detail 3 -B '~u /api/Users & ~c 200'")
# If 200 without auth header -> potential auth bypass
```

### Test IDOR
```python
# Modify user ID in request and replay
result = await mitmdump("-nr capture.mitm --map-remote '|/api/Users/1|/api/Users/2|' --flow-detail 3")
```

## Important Notes

- `-n` = no upstream connection (offline analysis)
- `-r` = read from file
- `-w` = write to file
- `-B` = filter expression
- `--flow-detail` = verbosity level (use 3 for testing)
- Capture files are binary `.mitm` format (not human-readable text)
- You can chain multiple operations: read, filter, modify, write
