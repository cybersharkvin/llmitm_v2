# mitmproxy.addonmanager

## Functions

### `_get_name(itm)`
Retrieves the name attribute from an item, or returns the lowercased class name if unavailable.

### `cut_traceback(tb, func_name)`
Reduces a traceback by excluding frames up to and including the specified function.

**Parameters:**
- `tb`: traceback object from `sys.exc_info()[2]`
- `func_name`: function name to cut at

**Returns:** Reduced traceback object

### `safecall()`
Context manager that catches exceptions and logs addon errors while allowing `AddonHalt` and `OptionsError` to propagate.

### `traverse(chain)`
Recursively yields all addons in a chain, including sub-addons.

**Parameters:**
- `chain`: addon chain to traverse

---

## Classes

### `Loader`
Passed to the load event when addons initialize, enabling configuration via options and commands.

**Attributes:**
- `master`: Reference to the master instance

#### `add_option(name, typespec, default, help, choices=None) -> None`
Registers a new option with mitmproxy.

**Parameters:**
- `name: str` - Option identifier
- `typespec: type` - Data type specification
- `default: Any` - Default value
- `help: str` - Single-paragraph description (no linebreaks)
- `choices: Sequence[str] | None` - Optional allowed values

#### `add_command(path, func) -> None`
Adds a command to mitmproxy. Using the `@mitmproxy.command.command` decorator is preferred for typical use cases.

**Parameters:**
- `path: str` - Command path
- `func: Callable` - Command function

---

### `LoadHook(hooks.Hook)`
Dataclass representing the load event, invoked when an addon is first loaded with access to the Loader object.

**Attributes:**
- `loader: Loader` - Configuration loader instance

---

### `AddonManager`
Manages addon registration, lifecycle, and event dispatching across the addon chain.

#### `__init__(master)`
Initializes the addon manager with an empty chain and lookup table.

#### `clear()`
Removes all registered addons and triggers their done hook.

#### `get(name)`
Retrieves an addon by name.

**Returns:** Addon instance or `None`

#### `register(addon)`
Registers an addon, triggers its load event, and registers sub-addons. Must be called within an active context.

**Returns:** The registered addon

#### `add(*addons)`
Appends addons to the chain and runs their load event.

#### `remove(addon)`
Unregisters an addon and its sub-addons, triggering the done hook.

#### `handle_lifecycle(event: hooks.Hook)` → async
Processes lifecycle events and triggers update hooks for Flow objects.

#### `invoke_addon(addon, event: hooks.Hook)` → async
Asynchronously invokes an event on an addon and descendants, supporting both sync and async handlers.

#### `invoke_addon_sync(addon, event: hooks.Hook)`
Synchronously invokes an event. Raises an error if the handler is async.

#### `trigger_event(event: hooks.Hook)` → async
Asynchronously dispatches an event across all addons in the chain, halting on `AddonHalt`.

#### `trigger(event: hooks.Hook)`
Synchronously dispatches events. The async variant `trigger_event()` is recommended.

#### `__len__()` → int
Returns the number of addons in the chain.

#### `__str__()` → str
Returns a formatted string representation of the addon chain.

#### `__contains__(item)` → bool
Checks if an addon is registered by name.