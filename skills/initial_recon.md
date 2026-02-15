# Initial Reconnaissance Methodology

## When to Use

Use this skill when you have NO prior knowledge of the target. This is the first-contact
scoping phase where you discover what the application is, what it does, and where its
attack surface lies.

## The Assumption-Gap Framework

Every vulnerability exists because of a gap between what someone intended and what code enforces:

1. **Business Intent**: "Only the account owner should see their profile data"
2. **Developer Assumption**: "The frontend only sends the logged-in user's ID, so we don't need to check"
3. **Code Enforcement**: Server returns any user's data for any valid ID — no ownership check
4. **The Gap**: Business says "owner only", code says "any authenticated user" — IDOR

Your job is to find these gaps by reading the traffic.

## Phase 1: Surface Area Mapping

Use `response_inspect` with no filter to get the full flow summary:

```python
overview = await response_inspect(mitm_file=mitm_file)
print(overview)
```

From the overview, identify:
- Which endpoints exist and what HTTP methods they use
- Which endpoints require auth (has_auth field)
- What content types are returned (JSON API vs HTML pages)
- Status code patterns (200s, 401s, 403s, 500s)

## Phase 2: Identity & Auth Analysis

Use `jwt_decode` to understand the authenticated user:

```python
tokens = await jwt_decode(mitm_file=mitm_file)
print(tokens)
```

From the JWT claims, identify:
- User ID, email, role fields
- Token expiration and issuer
- What permissions or scopes are encoded
- Whether the token is self-contained (all data in JWT) or opaque (needs server lookup)

## Phase 3: Endpoint Deep Dive

Use `response_inspect` with endpoint_filter to drill into interesting endpoints:

```python
users = await response_inspect(mitm_file=mitm_file, endpoint_filter="/api/Users")
print(users)
```

For each interesting endpoint, note:
- What data is returned in the response body
- What parameters are accepted
- Whether IDs appear in the URL path
- Whether the response contains data belonging to other users

## Phase 4: Security Posture

Use `header_audit` to assess the organization's security maturity:

```python
audit = await header_audit(mitm_file=mitm_file)
print(audit)
```

Missing security headers suggest:
- No CSP → possible XSS vectors
- No HSTS → possible downgrade attacks
- Permissive CORS → possible cross-origin data theft
- Server version leaks → known vulnerability lookup

## Phase 5: Behavioral Comparison

Use `response_diff` to compare flows and spot where auth state changes behavior:

```python
diff = await response_diff(mitm_file=mitm_file, flow_index_a=0, flow_index_b=3)
print(diff)
```

Key patterns to look for:
- Same endpoint, different auth → different data (IDOR indicator)
- Auth'd vs unauth'd → same data (missing auth check)
- Different status codes for same endpoint → inconsistent enforcement

## Prescribing Exploit Tools

Based on your observations, prescribe the right exploit tool:

| Observation | Suspected Gap | Exploit Tool |
|-------------|---------------|-------------|
| User data returned without ownership check | "Frontend sends correct ID" assumption | idor_walk |
| Endpoint returns data without auth header | "Auth middleware covers all routes" assumption | auth_strip |
| Same data returned for different user tokens | "Token identity is checked" assumption | token_swap |
| Admin-path endpoints accessible | "Admin routes are protected" assumption | namespace_probe |
| Role field in request body as plain string | "Roles are server-managed" assumption | role_tamper |

## Output Requirements

Each AttackOpportunity MUST include:
1. Which recon tool surfaced the evidence (recon_tool_used)
2. Specific data from the tool output (observation)
3. The business intent → developer assumption → enforcement gap (suspected_gap)
4. Which exploit tool to run and the specific target endpoint (recommended_exploit, exploit_target)
5. Why this exploit + target tests the gap (exploit_reasoning)
