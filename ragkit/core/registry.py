from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ragkit.core.base import Plugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, type[Plugin]] = {}

    def register(self, name: str, plugin_class: type[Plugin]) -> None:
        self._plugins[name] = plugin_class

    def get(self, name: str) -> type[Plugin] | None:
        return self._plugins.get(name)

    def load_entry_points(self, group: str = "ragkit.plugins") -> None:
        for ep in importlib.metadata.entry_points(group=group):
            try:
                plugin_class = ep.load()
                self.register(ep.name, plugin_class)
            except Exception:
                pass

    def all(self) -> dict[str, type[Any]]:
        return dict(self._plugins)
