---
paths:
  - "tests/**/*.py"
---

# Testing Philosophy Rule

This rule enforces the mandatory testing philosophy for all tests in the LLMitM v2 project.

## Mandatory Rules for All Tests

### 1. Max 5 Lines Per Test Body
Every test function MUST have a body of **5 lines or fewer** (excluding docstrings and decorators).

- Use fixtures to reduce setup boilerplate
- Keep test logic focused and concise
- Use helper functions for common setup patterns

**Example (✅ compliant - 4 lines):**
```python
def test_fingerprint_hash_is_deterministic():
    fp1 = Fingerprint(tech_stack="Express.js", auth_model="JWT", endpoint_pattern="/api/*")
    fp2 = Fingerprint(tech_stack="Express.js", auth_model="JWT", endpoint_pattern="/api/*")
    assert fp1.ensure_hash() == fp2.ensure_hash()
```

**Example (❌ non-compliant - 9 lines of test body):**
```python
def test_fingerprint_hash_computation():
    fp = Fingerprint(tech_stack="Express.js", auth_model="JWT", endpoint_pattern="/api/*")
    hash1 = fp.ensure_hash()
    assert fp.hash is not None
    assert len(fp.hash) == 64
    fp2 = Fingerprint(tech_stack="Express.js", auth_model="JWT", endpoint_pattern="/api/*")
    hash2 = fp2.ensure_hash()
    assert hash1 == hash2
    assert isinstance(hash1, str)
```

### 2. No Mocks or Fake Objects
NEVER use mocking libraries or mock-like functionality. Test with real code:
- ❌ `unittest.mock`, `Mock`, `MagicMock`, `patch`
- ❌ `pytest-mock` and `mocker` fixture
- ❌ `pytest.MonkeyPatch` for replacing real code
- ❌ Fake objects or test doubles
- ✅ Real Pydantic model instantiation and method calls
- ✅ Real Neo4j connections (with graceful skip if unavailable)
- ✅ Real `json` module for serialization
- ✅ Real `httpx` client for HTTP calls

**Example (✅ real behavior from user perspective):**
```python
def test_step_serialization():
    step = Step(order=1, phase=StepPhase.MUTATE, type=StepType.SHELL_COMMAND, command="python exploit.py")
    step2 = Step(**step.model_dump())
    assert step2 == step
```

**Example (✅ real model validation):**
```python
def test_action_graph_creation_with_steps():
    steps = [Step(order=0, phase=StepPhase.CAPTURE, type=StepType.HTTP_REQUEST, command="curl http://target")]
    ag = ActionGraph(id="test-1", vulnerability_type="IDOR", description="Test IDOR", steps=steps)
    assert ag.vulnerability_type == "IDOR" and len(ag.steps) == 1
```

**Example (❌ do not write - uses mocks):**
```python
def test_save_fingerprint(mocker):
    mock_driver = mocker.MagicMock()
    repo = GraphRepository(mock_driver)
    fp = Fingerprint(tech_stack="Express.js", auth_model="JWT", endpoint_pattern="/api/*")
    repo.save_fingerprint(fp)
    mock_driver.session.assert_called_once()
```

### 3. User Perspective Only
Test the library as an external user would call it. Never test internal implementation:
- ✅ Call public APIs and methods from the library
- ✅ Assert on observable outputs and model state
- ✅ Create instances and invoke methods normally
- ❌ Access private attributes or `_internal` methods
- ❌ Inspect function call counts or arguments
- ❌ Replace internals with test doubles
- ❌ Spy on method calls

**Example (✅ user perspective - calling public API):**
```python
def test_finding_creation():
    finding = Finding(observation="SQL injection vulnerability", severity="high", evidence_summary="Injected: admin=true")
    assert finding.severity == "high" and "SQL" in finding.observation
```

**Example (✅ user perspective - using model round-trip):**
```python
def test_critic_feedback_serialization():
    feedback = CriticFeedback(passed=True, feedback="Graph looks good")
    data = feedback.model_dump()
    feedback2 = CriticFeedback(**data)
    assert feedback2.passed is True
```

**Example (❌ do not write - tests internals):**
```python
def test_fingerprint_hash_algorithm():
    from llmitm_v2.models.fingerprint import _sha256_hash
    result = _sha256_hash("test")
    assert len(result) == 64
```

### 4. Graceful Skips for External Dependencies
If a test requires an external service (Neo4j, HTTP endpoints), skip gracefully when unavailable:
- Use `pytest.skip(reason)` for graceful skips
- Document why the skip is necessary
- Never fail tests because services are unavailable

**Example (✅ graceful skip for Neo4j integration test):**
```python
@pytest.mark.integration
def test_save_and_retrieve_fingerprint(neo4j_driver):
    repo = GraphRepository(neo4j_driver)
    fp = Fingerprint(tech_stack="Express.js", auth_model="JWT", endpoint_pattern="/api/*")
    fp.ensure_hash()
    repo.save_fingerprint(fp)
    retrieved = repo.get_fingerprint_by_hash(fp.hash)
    assert retrieved.hash == fp.hash
```

Where the fixture handles graceful skip:
```python
@pytest.fixture
def neo4j_driver():
    try:
        driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
        driver.verify_connectivity()
        return driver
    except Exception:
        pytest.skip("Neo4j instance unavailable")
```

### 5. Mark Integration Tests
Tests requiring external services MUST be marked with `@pytest.mark.integration`:

```python
@pytest.mark.integration
def test_action_graph_neo4j_storage(neo4j_driver):
    repo = GraphRepository(neo4j_driver)
    ag = ActionGraph(id="test-graph", vulnerability_type="IDOR", description="Test", steps=[])
    repo.save_action_graph("hash123", ag)
```

```python
@pytest.mark.integration
def test_http_target_fingerprinting():
    response = httpx.get("http://localhost:3000/api/health")
    assert response.status_code == 200
```

Run integration tests separately:
```bash
pytest tests/ -m integration  # Run only integration tests
pytest tests/ -m "not integration"  # Run only unit tests
```

## What This Means in Practice

| Scenario | What to Do |
|----------|-----------|
| **Testing Pydantic model creation** | Instantiate real models: `Step(order=0, phase=StepPhase.CAPTURE, ...)` |
| **Testing model validation** | Create instances and let Pydantic validate: `ActionGraph(...).ensure_id()` |
| **Testing serialization** | Use real `model_dump()`, `model_dump_json()`: `json.loads(ag.model_dump_json())` |
| **Testing Neo4j queries** | Use real `GraphRepository` with real driver (skip if unavailable) |
| **Testing error handling** | Trigger real errors by calling code normally, catch real exceptions |
| **Testing dependency injection** | Pass real instances to constructors and functions |

## Rationale

This testing philosophy exists because:

1. **Tests must verify user experience** — Real tests confirm how users will actually use the library
2. **Real behavior is truth** — The real code is the specification
3. **Simplicity** — Real tests are often simpler than elaborate mock setups
4. **Confidence** — Tests using real code give genuine confidence
5. **Maintenance** — When code changes, real tests break; mock tests pass silently with wrong behavior

## Enforcement

- Review tests manually before committing for compliance
- Keep tests small and focused (max 5 lines helps enforce this!)
- If a test feels like it needs mocks, that's a signal to refactor the code instead

---

**Reference**: See `CLAUDE.md` and `systemPatterns.md` for complete testing philosophy and architectural context.
