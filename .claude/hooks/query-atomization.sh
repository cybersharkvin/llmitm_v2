#!/bin/bash

# Atomizer Hook - Opt-in query atomization via Claude subagent
# Prefix prompt with "ea " to enable. All other prompts skip instantly.
# Debug: .claude/atomDebug.json | Output: .claude/memory/task.json

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
TASK_FILE="$PROJECT_DIR/.claude/memory/task.json"
DEBUG_FILE="$PROJECT_DIR/.claude/atomDebug.json"

# 1. Read hook input
input_json=$(cat)
echo "$input_json" | jq -e '.' >/dev/null 2>&1 || exit 0
user_prompt=$(echo "$input_json" | jq -r '.prompt // empty')

# 2. Only run when explicitly enabled with 'ea ' prefix
[[ "$user_prompt" == ea\ * ]] || exit 0
actual_prompt="${user_prompt#ea }"
[[ -n "$actual_prompt" ]] || exit 0

# 3. Prerequisites
command -v claude &>/dev/null || exit 0
AGENT_FILE="$PROJECT_DIR/.claude/agents/atom.md"
[[ -f "$AGENT_FILE" ]] || exit 0
AGENT_CONTENT=$(cat "$AGENT_FILE" 2>/dev/null)
[[ -n "$AGENT_CONTENT" ]] || exit 0

# 4. JSON schema — NOTE: additionalProperties:false silently breaks Claude Code CLI structured output
JSON_SCHEMA='{
  "type": "object",
  "properties": {
    "task": { "type": "string" },
    "assumptions": {
      "type": "array",
      "items": { "type": "string" }
    },
    "objectives": {
      "type": "object",
      "properties": {
        "primary": { "type": "array", "items": { "type": "string" } },
        "supporting": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["primary", "supporting"]
    },
    "dependencies": {
      "type": "object",
      "properties": {
        "prerequisites": { "type": "array", "items": { "type": "string" } },
        "constraints": { "type": "array", "items": { "type": "string" } },
        "sequential": { "type": "array", "items": { "type": "string" } },
        "parallel": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["prerequisites", "constraints", "sequential", "parallel"]
    },
    "atomic_actions": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "step": { "type": "integer" },
          "phase": { "type": "string" },
          "type": { "type": "string", "enum": ["task", "checkpoint", "decision_point"] },
          "action": { "type": "string" },
          "input": { "type": "string" },
          "output": { "type": "string" },
          "file": { "type": "string" },
          "depends_on": { "type": "array", "items": { "type": "integer" } }
        },
        "required": ["step", "phase", "type", "action", "input", "output"]
      },
      "minItems": 1
    },
    "success_criteria": {
      "type": "object",
      "properties": {
        "per_step": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "step": { "type": "integer" },
              "criterion": { "type": "string" },
              "measurable": { "type": "boolean" }
            },
            "required": ["step", "criterion", "measurable"]
          }
        },
        "overall": { "type": "string" },
        "quality_standards": { "type": "array", "items": { "type": "string" } },
        "acceptance_criteria": { "type": "array", "items": { "type": "string" } }
      },
      "required": ["per_step", "overall", "quality_standards", "acceptance_criteria"]
    }
  },
  "required": ["task", "assumptions", "objectives", "dependencies", "atomic_actions", "success_criteria"]
}'

# 5. Call haiku in separate context
RESULT=$(cd "$PROJECT_DIR" && echo "$actual_prompt" | timeout 180 claude -p \
  --agent atom \
  --setting-sources user \
  --output-format json \
  --json-schema "$JSON_SCHEMA" 2>&1)
EXIT_CODE=$?

# 6. Write debug log (hook input + raw response)
RESULT_JSON="$RESULT"
echo "$RESULT" | jq -e '.' >/dev/null 2>&1 || RESULT_JSON='"'"$(echo "$RESULT" | head -c 2000)"'"'
jq -n \
  --arg ts "$(date -Iseconds)" \
  --argjson hook_input "$input_json" \
  --arg actual "$actual_prompt" \
  --argjson response "$RESULT_JSON" \
  --argjson exit_code "$EXIT_CODE" \
  '{timestamp: $ts, hook_input: $hook_input, actual_prompt: $actual, response: $response, exit_code: $exit_code}' \
  > "$DEBUG_FILE" 2>/dev/null

# 7. Write task.json from structured_output
if [[ $EXIT_CODE -eq 0 ]]; then
  TASK_JSON=$(echo "$RESULT" | jq '.structured_output // empty' 2>/dev/null)
  if [[ -n "$TASK_JSON" && "$TASK_JSON" != "null" ]]; then
    echo "$TASK_JSON" > "$TASK_FILE"
  fi
fi

# 8. Return execution contract
jq -n '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: "You MUST read @.claude/memory/task.json IMMEDIATELY before proceeding. Follow the atomic_actions array in exact dependency order. Validate each step against its success_criteria before marking complete."
  }
}'
