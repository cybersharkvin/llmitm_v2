# Finding Persistence & Validation

## When to Use

Use this skill when you have identified a potential vulnerability and MUST verify it is
reproducible before including it in the attack plan. A finding that cannot be reproduced
is worthless.

## Validation Methodology

### Step 1: Verify Evidence Quality

Re-examine the tool output that surfaced the finding:

```python
# Re-run the recon tool that found the issue
detail = await response_inspect(mitm_file=mitm_file, endpoint_filter="/api/vulnerable_endpoint")
print(detail)
# Verify the response body actually contains the sensitive data you claimed
```

### Step 2: Check for False Positives

Common false positives:
- **200 OK but empty body**: Endpoint exists but doesn't leak data
- **Different user's data looks the same**: Generic responses vs actual IDOR
- **Cached responses**: Server returning stale data
- **Permissive CORS but no sensitive data**: CORS misconfiguration without impact

Use `response_diff` to verify different responses for different contexts:

```python
diff = await response_diff(mitm_file=mitm_file, flow_index_a=2, flow_index_b=6)
print(diff)
# If body_identical=true, this might be a false positive
```

### Step 3: Assess Determinism

A finding is suitable for an ActionGraph (deterministic execution) if:
- It does NOT depend on timing or race conditions
- It does NOT require a specific server state that may change
- The same request sequence will produce the same result every time
- The success criteria can be expressed as a regex or status code match

### Step 4: Establish Impact

Rate each finding by:
1. **Confidentiality**: Does it expose sensitive data?
2. **Integrity**: Can it modify data belonging to others?
3. **Availability**: Can it disrupt service?
4. **Authentication bypass**: Does it skip auth entirely?

## Prescribing Exploit Tools

Only prescribe an exploit tool if:
1. The evidence is specific (cites exact response data, not vague observations)
2. The gap is clear (you can name the business intent and the missing enforcement)
3. The exploit is deterministic (same inputs → same outputs every time)
4. The target endpoint is specific (exact path, not a category)

## Output Requirements

For each validated finding:
1. Exact endpoint and evidence from recon tools
2. Expected response pattern (regex for success_criteria)
3. Whether it requires specific preconditions (auth, prior requests)
4. Determinism assessment: can this be encoded as a repeatable exploit?
