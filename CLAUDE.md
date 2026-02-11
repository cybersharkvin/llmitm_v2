# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MANDATORY: Read Memory Files First

**At the start of EVERY session, you MUST read all memory files before doing any work:**

@.claude/memory/activeContext.json
@.claude/memory/projectBrief.md
@.claude/memory/systemPatterns.md
@.claude/memory/techContext.md
@.claude/memory/neo4jSchema.md
@.claude/memory/strandsGuide.md
@.claude/memory/projectProgress.md
@.claude/memory/tags.md

**Do not skip this step.** These files contain persistent context that survives between sessions.

---

## Memory File System

This project uses a memory file system for persistent context across Claude Code sessions.

### The Two-Part System

- **Memory files** (`.claude/memory/*.md`) = **Context** — WHY patterns exist, HOW systems work, PURPOSE of implementations
- **tags.md** = **Inventory** — WHAT exists, WHERE it's located (auto-generated)

### The Eight Memory Files

| File | Purpose |
|------|---------|
| `activeContext.md` | Current working state, recent changes, immediate next steps |
| `projectBrief.md` | Project goals, scope, requirements |
| `systemPatterns.md` | Architectural patterns and design decisions |
| `techContext.md` | Tech stack, dependencies, constraints |
| `neo4jSchema.md` | Complete Neo4j schema, queries, and integration patterns |
| `strandsGuide.md` | Strands SDK integration patterns and usage examples |
| `projectProgress.md` | Completed features, known issues, technical debt |
| `tags.md` | Auto-generated codebase inventory (**never edit manually**) |

---

## When to Update Memory Files

### `activeContext.json` — Update FREQUENTLY

**Update after:**
- Completing any significant task or feature
- Making architectural decisions
- Discovering important issues or blockers
- Changing working focus or context
- End of every work session

**Structure (follow this format exactly):**
```json
{
  "session": "Phase name and date",
  "completed_phase": "What phase just finished",
  "summary": "One-line summary of work",
  "files_created": N,
  "git_commit": "commit hash",
  "files_by_category": {
    "category_name": [
      {"path": "file/path.py", "description": "What it does"}
    ]
  },
  "test_results": {
    "test_suite": "tests/test_X.py",
    "passed": N,
    "failed": 0,
    "status": "✅ ALL PASSING or ⚠️ ISSUES",
    "coverage": ["test area 1", "test area 2"],
    "notes": "Important notes"
  },
  "design_decisions": [
    {"decision": "Name", "rationale": "Why chosen"}
  ],
  "next_phases": [
    {
      "phase": "Phase N: Name",
      "estimated_hours": N,
      "tasks": ["Task 1", "Task 2"]
    }
  ],
  "blockers": "None or description",
  "context_for_next_session": ["context point 1", "context point 2"],
  "files_to_reference": ["file.md — description"]
}
```

**Keep it current** — This is the "working memory" for the next session. Use the JSON format to organize information clearly with specific categories for files, test results, design decisions, and next steps.

---

### `projectProgress.md` — Update after COMPLETING features

**Update after:**
- Finishing a feature (move from "In Progress" to "Completed")
- Discovering bugs or technical debt
- Identifying new known issues
- Major milestones

**Include:**
- Completion dates for features
- Known issues with priority
- Technical debt items with reasoning

---

### `systemPatterns.md` — Update after ESTABLISHING patterns

**Update after:**
- Creating new architectural patterns
- Establishing coding conventions
- Making significant design decisions
- Adding new integration patterns

**Include:**
- Pattern name and purpose
- When to use the pattern
- Key files/functions involved
- Why this pattern was chosen

---

### `techContext.md` — Update after CHANGING dependencies

**Update after:**
- Adding new dependencies
- Removing dependencies
- Updating configuration files
- Changing build/test commands
- Modifying environment variables

**Include:**
- Dependency name and version
- Why it was added
- How it's used
- Any configuration needed

---

### `projectBrief.md` — Update RARELY

**Update only when:**
- Project scope fundamentally changes
- Core requirements are added/removed
- Success criteria change

**This file should remain stable** — only update for major scope changes.

---

### `tags.md` — NEVER edit manually

This file is auto-generated. It provides codebase inventory:
- Component locations
- Function signatures
- Interface definitions
- Configuration mappings

**Always check tags.md before creating new code** to avoid duplication.

---

## What NOT to Include in Memory Files

- Duplicate information across files
- Implementation details that belong in code comments
- Temporary debugging notes
- Content already in tags.md (file locations, function lists)
- Verbose explanations when concise ones suffice