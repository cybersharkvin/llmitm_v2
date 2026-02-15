# Agent Skills

> Source: https://platform.claude.com/docs/en/build-with-claude/skills-guide

Extend Claude's capabilities through organized folders of instructions, scripts, and resources via the code execution tool.

---

**Status**: Beta. Requires beta headers: `code-execution-2025-08-25`, `skills-2025-10-02`, `files-api-2025-04-14`.

## Overview

Skills are organized instruction/resource bundles that Claude loads into a code execution container. Two sources:

| Aspect | Anthropic Skills | Custom Skills |
|--------|------------------|---------------|
| Type | `anthropic` | `custom` |
| IDs | Short names: `pptx`, `xlsx`, `docx`, `pdf` | Generated: `skill_01Abc...` |
| Versions | Date-based: `20251013` or `latest` | Epoch timestamp or `latest` |
| Management | Pre-built by Anthropic | Upload via Skills API |

## Using Skills in Messages

Specify skills in the `container` parameter (up to 8 per request):

```python
response = client.beta.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    betas=["code-execution-2025-08-25", "skills-2025-10-02"],
    container={
        "skills": [{"type": "anthropic", "skill_id": "pptx", "version": "latest"}]
    },
    messages=[{"role": "user", "content": "Create a presentation about renewable energy"}],
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
)
```

## How Skills Load

1. Claude sees metadata (name, description) in system prompt
2. Skill files copied into container at `/skills/{directory}/`
3. Claude automatically loads and uses relevant skills
4. Multiple skills compose together

## Managing Custom Skills

### Create

```python
from anthropic.lib import files_from_dir

skill = client.beta.skills.create(
    display_title="Financial Analysis",
    files=files_from_dir("/path/to/skill"),
    betas=["skills-2025-10-02"],
)
```

Requirements: Must include `SKILL.md` at top level. Total upload < 8MB.

### Version, List, Delete

Skills support versioning. Use `"latest"` for dev, pin specific versions for production.

## Constraints

- No network access from skill containers
- No runtime package installation
- Each request gets a fresh container (unless reusing container ID)
- Max 8 skills per request
- Max 8MB upload size

## Relevance to Our Project

Agent Skills are a higher-level abstraction for organizing tool instructions. Not directly applicable to our current architecture (we use custom tools via the Messages API directly), but useful reference for understanding Anthropic's vision for composable agent capabilities.
