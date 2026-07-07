"""
Minimal in-memory database layer used by the sample application.
"""

from typing import Any, Dict, Optional


class InMemoryDatabase:
    """A toy key-value store standing in for a real database connection."""

    def __init__(self):
        self._store: Dict[str, Any] = {}

    def put(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def all_keys(self):
        return list(self._store.keys())
