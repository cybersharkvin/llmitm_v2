"""Mitmdump tool for programmatic tool calling.

Defines the tool schema and handler for the mitmdump tool used by ProgrammaticAgent.
The agent writes Python in Anthropic's code_execution sandbox; when it calls
`await mitmdump(...)`, our handler runs the actual subprocess on the host.
"""

import shlex
import subprocess
import sys
from pathlib import Path

# Tool schema for Anthropic API — used by ProgrammaticAgent
MITMDUMP_TOOL_SCHEMA = {
    "name": "mitmdump",
    "description": (
        "Execute a mitmdump command. Returns stdout and stderr. "
        "See skill guides in system prompt for flags and filters. "
        "Example: mitmdump -nr capture.mitm --flow-detail 3 -B '~u /api/'"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "mitmdump CLI arguments (do NOT include 'mitmdump' prefix)",
            }
        },
        "required": ["command"],
    },
    "allowed_callers": ["code_execution_20250825"],
}

# Resolve mitmdump binary from the same venv as the running Python
_MITMDUMP_BIN = str(Path(sys.executable).parent / "mitmdump")


def handle_mitmdump(command: str) -> str:
    """Execute mitmdump with given arguments. Returns truncated stdout + stderr.

    Args:
        command: CLI arguments for mitmdump (without 'mitmdump' prefix)

    Returns:
        Formatted string with STDOUT and STDERR sections
    """
    args = [_MITMDUMP_BIN] + shlex.split(command)
    result = subprocess.run(
        args,
        capture_output=True,
        timeout=30,
    )
    stdout = result.stdout.decode(errors="replace")[:4000]
    stderr = result.stderr.decode(errors="replace")[:1000]
    return f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
