# Placeholder — wire up a real Redis client (e.g. redis-py) here when needed.
# For now this is a simple in-process dict cache.

from typing import Any, Optional


class SimpleCache:
    def __init__(self):
        self._store: dict = {}

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)
