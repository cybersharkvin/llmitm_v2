# mitmproxy.coretypes.multidict

## Overview

The `multidict` module provides dictionary-like data structures that support multiple values per key. This is useful for scenarios like HTTP headers where a single key may have multiple associated values.

## Classes

### `_MultiDict[KT, VT]`

Abstract base class implementing a mutable mapping with support for multiple values per key.

**Attributes:**
- `fields: tuple[tuple[KT, VT], ...]` — The underlying raw datastructure storing key-value pairs.

**Abstract Methods:**
- `_reduce_values(values: Sequence[VT]) -> VT` — Reduces multiple values for a key to a single value (e.g., taking the first value or folding headers).
- `_kconv(key: KT) -> KT` — Converts a key to its canonical representation (e.g., lowercasing for case-insensitive keys).

**Public Methods:**

```python
def get_all(key: KT) -> list[VT]
```
Returns all values for a given key as a list. Empty list if key not found.

```python
def set_all(key: KT, values: list[VT]) -> None
```
Replaces all existing values for a key with new ones.

```python
def add(key: KT, value: VT) -> None
```
Appends an additional value for the given key at the end.

```python
def insert(index: int, key: KT, value: VT) -> None
```
Inserts an additional value for the given key at a specific position.

```python
def keys(multi: bool = False)
```
Returns keys. When `multi=True`, returns one key per value; when `False`, returns each unique key once.

```python
def values(multi: bool = False)
```
Returns values. When `multi=True`, returns all values; when `False`, returns the first value per key.

```python
def items(multi: bool = False)
```
Returns (key, value) tuples. When `multi=True`, returns all pairs; when `False`, returns one pair per unique key.

---

### `MultiDict[KT, VT]`

Concrete implementation of `_MultiDict` that stores its own data. Implements serialization support.

**Constructor:**
```python
def __init__(self, fields=())
```
Initializes with an optional sequence of (key, value) tuples.

**Methods:**

```python
def get_state(self)
```
Returns the fields for serialization.

```python
def set_state(self, state)
```
Restores fields from serialized state.

```python
@classmethod
def from_state(cls, state)
```
Creates a new instance from serialized state.

**Inherited Methods:** All methods from `_MultiDict` are available.

---

### `MultiDictView[KT, VT]`

A view over external data that provides the `_MultiDict` interface without storing state. Data is retrieved from and written back to a parent object via getter/setter functions.

**Constructor:**
```python
def __init__(self, getter, setter)
```
- `getter` — Callable that returns the current fields tuple.
- `setter` — Callable that accepts and stores an updated fields tuple.

**Methods:**

```python
@property
def fields(self) -> tuple[tuple[KT, VT], ...]
```
Dynamically retrieves fields from the getter.

```python
def copy(self) -> MultiDict[KT, VT]
```
Creates a standalone `MultiDict` copy of the current view data.

**Inherited Methods:** All methods from `_MultiDict` are available.
