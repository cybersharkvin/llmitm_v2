"""Human-in-the-loop approval hook for destructive actions.

Intercepts tool calls and requests user approval for operations that could
modify application state or compromise systems.
"""

from typing import Any

try:
    from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry
except ImportError:
    # Graceful fallback when Strands is not installed
    HookProvider = object  # type: ignore
    BeforeToolCallEvent = None  # type: ignore
    HookRegistry = None  # type: ignore


class ApprovalHook(HookProvider):
    """Hook provider for destructive action approval via Strands.

    Monitors tool calls and interrupts execution for patterns that indicate
    destructive or sensitive operations (DELETE, PATCH, modifying credentials, etc.).
    """

    def __init__(self, destructive_patterns: list[str] | None = None):
        """Initialize hook with destructive patterns.

        Args:
            destructive_patterns: List of uppercase strings to detect in commands.
                                 Defaults to common destructive operations.
        """
        if destructive_patterns is None:
            destructive_patterns = [
                "DELETE",
                "DROP",
                "TRUNCATE",
                "UNINSTALL",
                "REMOVE",
                "KILL",
                "DESTROY",
                "WIPE",
                "RESET",
            ]
        self.destructive_patterns = destructive_patterns

    def register_hooks(self, registry: Any, **kwargs: Any) -> None:
        """Register BeforeToolCallEvent callback.

        Args:
            registry: Strands HookRegistry to register with
            **kwargs: Additional arguments (unused)
        """
        registry.add_callback(BeforeToolCallEvent, self.check_approval)

    def check_approval(self, event: Any) -> None:
        """Check if tool call requires approval.

        Intercepts BeforeToolCallEvent and cancels destructive operations
        unless explicitly approved by user.

        Args:
            event: Strands BeforeToolCallEvent with tool_use details
        """
        # Extract command/input from tool call
        tool_input = event.tool_use.get("input", {})
        command_str = str(tool_input).upper()

        # Check if any destructive pattern matches
        if any(pattern in command_str for pattern in self.destructive_patterns):
            # Request user approval
            approval = event.interrupt(
                "llmitm-approval",
                reason={
                    "tool": event.tool_use.get("name", "unknown"),
                    "input": tool_input,
                },
            )

            # Cancel if user denies
            if approval.lower() not in ("y", "yes", "approve"):
                event.cancel_tool = f"User denied destructive operation: {command_str}"
