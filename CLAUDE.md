# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MANDATORY: Read Memory Files First

**At the start of EVERY session, you MUST read all memory files BEFORE doing any work:**

@.claude/memory/tags.md
@.claude/memory/activeContext.json
@.claude/memory/projectBrief.md
@.claude/memory/systemPatterns.md
@.claude/memory/techContext.md
@.claude/memory/projectProgress.md


**This is not optional.** These files contain persistent context that survives between sessions and you MUST NOT skip this step.

---

## `@.claude/memory/tags.md` — Your Codebase Skeleton

`tags.md` is a high-level semantic map of the **entire** codebase:

- **Abstract Base Classes** — Core interfaces and contracts
- **Concrete Implementations** — Classes that inherit from ABCs
- **Factory Functions** — Functions that construct complex objects
- **All Classes** — Complete class inventory
- **All Functions** — Complete function inventory
- **All Methods** — Complete method inventory

1. You **MUST** read `tags.md` before beginning any work session
2. You **MUST** prioritize `tags.md` above all other memory files for semantic codebase awareness
3. Before creating ANY new code, you **SHOULD** grep `tags.md` to search for functions and APIs you are looking for
4. Before adding new functionality, you **SHOULD** search for existing related code by grepping expected function names, API calls, and opening files where that code may exist
5. You **SHOULD NOT** manually explore the codebase with broad directory scans unless **absolutely necessary** for the given task
6. You **MUST NOT** manually edit `tags.md` — it is auto-generated

**Why This Matters:**
Semantic awareness of the entire codebase at once prevents accidental duplication, reveals existing patterns you can follow, and enables you to work efficiently without exhaustive exploration.

---

## Memory File System

This project uses a memory file system for persistent context across Claude Code sessions.

### The Two-Part System

- **Memory files** (`.claude/memory/`) = **Context** — WHY patterns exist, HOW systems work, PURPOSE of implementations
- **tags.md** = **Inventory** — WHAT exists, WHERE it's located (auto-generated)

### Your Memory Files

| File | Purpose |
|------|---------|
| `activeContext.json` | Current working state, recent changes, immediate next steps |
| `projectBrief.md` | Project goals, scope, requirements |
| `systemPatterns.md` | Architectural patterns and design decisions |
| `techContext.md` | Tech stack, dependencies, constraints |
| `projectProgress.md` | Completed features, known issues, technical debt |
| `tags.md` | Auto-generated codebase inventory (**never edit manually**) |

---

## `tags.md` — MUST NOT be edited manually

This file is auto-generated. It provides codebase inventory:
- Component locations
- Function signatures
- Interface definitions
- Configuration mappings

**You MUST check tags.md before creating new code to avoid duplication. Failure to do so WILL result in code duplication.**

## When to Update Memory Files

### `activeContext.json` — MUST be updated FREQUENTLY

**Update MUST occur after:**
- Completing any significant task or feature
- Making architectural decisions
- Discovering important issues or blockers
- Changing working focus or context
- End of every work session

**Structure MUST follow this format exactly:**
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

**You MUST keep it current** — This is the "working memory" for the next session. You MUST use the JSON format to organize information clearly with specific categories for files, test results, design decisions, and next steps.

---

### `projectProgress.md` — MUST be updated after COMPLETING features

**Update MUST occur after:**
- Finishing a feature (move from "In Progress" to "Completed")
- Discovering bugs or technical debt
- Identifying new known issues
- Major milestones

**You MUST include:**
- Completion dates for features
- Known issues with priority
- Technical debt items with reasoning

---

### `systemPatterns.md` — MUST be updated after ESTABLISHING patterns

**Update MUST occur after:**
- Creating new architectural patterns
- Establishing coding conventions
- Making significant design decisions
- Adding new integration patterns

**You MUST include:**
- Pattern name and purpose
- When to use the pattern
- Key files/functions involved
- Why this pattern was chosen

---

### `techContext.md` — MUST be updated after CHANGING dependencies

**Update MUST occur after:**
- Adding new dependencies
- Removing dependencies
- Updating configuration files
- Changing build/test commands
- Modifying environment variables

**You MUST include:**
- Dependency name and version
- Why it was added
- How it's used
- Any configuration needed

---

### `projectBrief.md` — MUST be updated RARELY

**Update ONLY when:**
- Project scope fundamentally changes
- Core requirements are added/removed
- Success criteria change

**This file MUST remain stable** — update ONLY for major scope changes.

---


## What MUST NOT be Included in Memory Files

You **MUST NOT** include:
- Duplicate information across files
- Implementation details that belong in code comments
- Temporary debugging notes
- Content already in tags.md (file locations, function lists)
- Verbose explanations when concise ones suffice

## MANDATORY: Read Memory Files First

**At the start of EVERY session, you MUST read all memory files BEFORE doing any work:**

@.claude/memory/tags.md
@.claude/memory/activeContext.json
@.claude/memory/projectBrief.md
@.claude/memory/systemPatterns.md
@.claude/memory/techContext.md
@.claude/memory/projectProgress.md

## `@.claude/memory/tags.md` — Your Codebase Skeleton

`tags.md` is a high-level semantic map of the **entire** codebase:

- **Abstract Base Classes** — Core interfaces and contracts
- **Concrete Implementations** — Classes that inherit from ABCs
- **Factory Functions** — Functions that construct complex objects
- **All Classes** — Complete class inventory
- **All Functions** — Complete function inventory
- **All Methods** — Complete method inventory

1. You **MUST** read `tags.md` before beginning any work session
2. You **MUST** prioritize `tags.md` above all other memory files for semantic codebase awareness
3. Before creating ANY new code, you **SHOULD** grep `tags.md` to search for functions and APIs you are looking for
4. Before adding new functionality, you **SHOULD** search for existing related code by grepping expected function names, API calls, and opening files where that code may exist
5. You **SHOULD NOT** manually explore the codebase with broad directory scans unless **absolutely necessary** for the given task
6. You **MUST NOT** manually edit `tags.md` — it is auto-generated

**Why This Matters:**
Semantic awareness of the entire codebase at once prevents accidental duplication, reveals existing patterns you can follow, and enables you to work efficiently without exhaustive exploration.
