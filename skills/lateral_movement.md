# Lateral Movement & Authorization Testing

## When to Use

Use this skill when you have authenticated access and MUST test what a user can reach
beyond their intended scope. This covers IDOR, privilege escalation, and access control
boundary testing.

## IDOR Testing Pattern

IDOR (Insecure Direct Object Reference) occurs when the application uses user-supplied
identifiers to access objects without verifying the requesting user owns them.

### Step 1: Identify Resource Endpoints

Use `response_inspect` to find endpoints with numeric or UUID identifiers:

```python
detail = await response_inspect(mitm_file=mitm_file, endpoint_filter="/api/Users/\\d+")
print(detail)
```

Look for: `/api/Users/{id}`, `/api/Orders/{id}`, `/api/Documents/{id}`

### Step 2: Understand Token Identity

Use `jwt_decode` to understand whose token is being used:

```python
tokens = await jwt_decode(mitm_file=mitm_file)
print(tokens)
# Note the user ID in the JWT claims vs the ID in the URL
```

### Step 3: Compare Responses

If the capture has requests to different IDs, use `response_diff`:

```python
diff = await response_diff(mitm_file=mitm_file, flow_index_a=2, flow_index_b=5)
print(diff)
# If body differs but both return 200 → IDOR likely
```

## Privilege Escalation Testing

### Vertical Escalation

Look for admin endpoints in the flow summary:

```python
overview = await response_inspect(mitm_file=mitm_file)
# Check for /admin, /api/admin, /dashboard paths
```

If admin endpoints return 200 with a regular user token → prescribe `namespace_probe`.

### Horizontal Escalation

Test if User A can perform User B's actions:
1. Identify resource ownership from JWT claims
2. Check if requests to other users' resources succeed
3. If yes → prescribe `idor_walk` or `token_swap`

## Role Manipulation

Look for role/privilege fields in request bodies:

```python
detail = await response_inspect(mitm_file=mitm_file, endpoint_filter="/register|/profile|/user")
print(detail)
# Check if request body contains "role", "isAdmin", "privilege" fields
```

If role field is in request body as plain string → prescribe `role_tamper`.

## Access Control Checklist

For each protected resource, verify:
- [ ] Cannot access without authentication (returns 401/403)
- [ ] Cannot access other users' resources (IDOR check)
- [ ] Cannot escalate to admin role
- [ ] Cannot modify other users' data
- [ ] Rate limiting prevents brute-force enumeration
- [ ] Deleted/disabled users cannot access resources

## Evidence Requirements

For each finding, you MUST provide:
1. The exact request that succeeded when it should have failed
2. The response status code and relevant body content
3. Which user's credentials were used
4. Which user's resource was accessed
5. Why this constitutes a security boundary violation
