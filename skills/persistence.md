# Finding Persistence & Validation

## When to Use

Use this skill when you have identified a potential vulnerability and MUST verify it is
reproducible before including it in the attack plan. A finding that cannot be reproduced
is worthless.

## Validation Methodology

### Step 1: Reproduce from Scratch

The vulnerability MUST be reproducible starting from a clean state:

```python
# Re-authenticate (don't reuse old tokens)
fresh_login = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u /login & ~m POST'")
# Extract fresh token

# Replay the exact sequence that triggered the finding
replay = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u /api/vulnerable_endpoint'")
# Verify same result
```

### Step 2: Test Time Sensitivity

Some findings are transient:
- Race conditions (timing-dependent)
- Cache poisoning (expires)
- Session fixation (session-dependent)

```python
# Test multiple times with delays
for i in range(3):
    result = await mitmdump(f"-nr {mitm_file} --flow-detail 3 -B '~u /api/target'")
    print(f"Attempt {i+1}: {result[:200]}")
```

### Step 3: Confirm Not a False Positive

Common false positives:
- **200 OK but empty body**: Endpoint exists but doesn't leak data
- **Different user's data looks the same**: Generic responses vs actual IDOR
- **Cached responses**: Server returning stale data
- **Permissive CORS but no sensitive data**: CORS misconfiguration without impact

### Step 4: Establish Impact

Rate each finding by:
1. **Confidentiality**: Does it expose sensitive data?
2. **Integrity**: Can it modify data belonging to others?
3. **Availability**: Can it disrupt service?
4. **Authentication bypass**: Does it skip auth entirely?

## Determinism Check

A finding is suitable for an ActionGraph (deterministic execution) if:
- It does NOT depend on timing or race conditions
- It does NOT require a specific server state that may change
- The same request sequence will produce the same result every time
- The success criteria can be expressed as a regex or status code match

If the finding is NOT deterministic, note this in the plan so the ActionGraph
can include retry logic or state verification steps.

## Output Requirements

For each validated finding:
1. Exact reproduction steps (request sequence)
2. Expected response (status code + body pattern)
3. Number of successful reproductions out of attempts
4. Whether it requires specific preconditions (auth, prior requests)
5. Determinism assessment: can this be encoded as a repeatable ActionGraph?
