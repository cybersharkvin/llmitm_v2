# Initial Reconnaissance Methodology

## When to Use

Use this skill when you have NO prior knowledge of the target. This is the first-contact
scoping phase where you discover what the application is, what it does, and where its
attack surface lies.

## Phase 1: Technology Fingerprinting

Analyze response headers to identify the tech stack:

1. **Server identification**: Look for `Server`, `X-Powered-By`, `X-AspNet-Version` headers
2. **Framework detection**: Error pages, default routes, cookie names reveal frameworks
3. **API format**: JSON vs XML vs GraphQL vs gRPC

```python
# Scan common entry points and collect headers
endpoints = ["/", "/api/", "/rest/", "/graphql", "/admin", "/swagger",
             "/health", "/api/health", "/status", "/.well-known/openid-configuration"]
results = {}
for ep in endpoints:
    resp = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u {ep}'")
    results[ep] = resp

# Summarize tech stack from headers
print("Tech stack indicators found:")
for ep, data in results.items():
    if "200" in data or "301" in data or "302" in data:
        print(f"  {ep}: LIVE")
```

## Phase 2: Authentication Model Discovery

1. **Identify auth endpoints**: `/login`, `/auth`, `/oauth`, `/token`, `/api/auth`
2. **Determine auth mechanism**:
   - `Authorization: Bearer` -> JWT tokens
   - `Set-Cookie: session=` -> Cookie-based sessions
   - `X-API-Key` -> API key auth
   - `WWW-Authenticate: Basic` -> HTTP Basic Auth
3. **Test auth enforcement**: Hit protected endpoints without credentials

## Phase 3: API Endpoint Mapping

1. **Common REST patterns**: `/api/v1/`, `/rest/`, `/v2/`
2. **Resource enumeration**: `/api/Users`, `/api/Products`, `/api/Orders`
3. **Admin endpoints**: `/admin`, `/api/admin`, `/dashboard`
4. **Documentation**: `/swagger`, `/api-docs`, `/openapi.json`
5. **Debug/info**: `/health`, `/status`, `/metrics`, `/env`, `/debug`

For each discovered endpoint, record:
- HTTP methods that work (GET, POST, PUT, DELETE)
- Whether it requires authentication
- What data it returns
- What parameters it accepts

## Phase 4: Security Signal Collection

Look for:
- **CORS**: `Access-Control-Allow-Origin: *` (permissive = weak)
- **CSP**: Missing `Content-Security-Policy` header
- **Rate limiting**: Repeated requests return same status (no 429)
- **Error verbosity**: Stack traces, SQL errors, file paths in responses
- **Information disclosure**: Version numbers, internal IPs, debug info

## Output Requirements

After completing recon, you MUST provide:
1. Identified tech stack with evidence
2. Authentication model with evidence
3. Complete endpoint map with methods and auth requirements
4. At least 2 attack opportunities ranked by confidence
5. Each opportunity MUST cite specific evidence from tool calls
