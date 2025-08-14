"""Simple plugin registry for ingest components."""

from __future__ import annotations

from typing import Any, Dict, Type


class Registry:
    def __init__(self) -> None:
        self._items: Dict[str, Any] = {}

    def register(self, name: str, item: Any) -> None:
        if name in self._items:
            raise ValueError(f"Item already registered: {name}")
        self._items[name] = item

    def get(self, name: str) -> Any:
        return self._items[name]

    def names(self) -> Dict[str, Any]:
        return dict(self._items)


GLOBAL_REGISTRY = Registry()


