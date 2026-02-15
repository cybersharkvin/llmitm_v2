# Recon Tools Reference

## Available Tools

### response_inspect
- **Purpose**: See what endpoints were hit and what came back
- **Without filter**: Returns summary of ALL flows (method, URL, status, auth, content_type)
- **With endpoint_filter**: Returns full detail for matching flows (headers, cookies, body)
- **Example**: `await response_inspect(mitm_file="capture.mitm")` for overview
- **Example**: `await response_inspect(mitm_file="capture.mitm", endpoint_filter="/api/Users")` for detail

### jwt_decode
- **Purpose**: Understand who the authenticated user is
- **Returns**: All flows with Bearer tokens + decoded JWT claims
- **Example**: `await jwt_decode(mitm_file="capture.mitm")`

### header_audit
- **Purpose**: Assess security posture across all endpoints
- **Checks**: Missing CSP/HSTS, permissive CORS, server version leaks, info disclosure
- **Example**: `await header_audit(mitm_file="capture.mitm")`

### response_diff
- **Purpose**: Compare two flows to spot behavioral differences
- **Use case**: Auth'd vs unauth'd same endpoint, or different user contexts
- **Example**: `await response_diff(mitm_file="capture.mitm", flow_index_a=2, flow_index_b=6)`

## Exploit Tools (prescribe in output, don't call)

| Tool | Tests | Prescribe When |
|------|-------|----------------|
| idor_walk | Resource access across user boundaries | ID-in-URL + different user data returned |
| auth_strip | Endpoints that work without auth | Protected data accessible without token |
| token_swap | Cross-user authorization | User A's token accesses User B's resources |
| namespace_probe | Unprotected admin/internal paths | Admin-prefix endpoints accessible without auth |
| role_tamper | Privilege escalation via body modification | Role/privilege field in request body as plain string |

## Workflow

1. `response_inspect` (no filter) — build mental map of surface area
2. `jwt_decode` — understand who the authenticated user is
3. `response_inspect` (with filter) — drill into interesting endpoints
4. `header_audit` — assess overall security posture
5. `response_diff` — compare auth states if relevant
6. Identify assumption gaps — prescribe exploit tools
