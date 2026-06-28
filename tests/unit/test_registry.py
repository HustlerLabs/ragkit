from __future__ import annotations

from ragkit.core.base import Plugin
from ragkit.core.registry import PluginRegistry


class _FakePlugin(Plugin):
    def register(self, agent) -> None:
        agent.registered = True


class TestPluginRegistry:
    def test_register_and_get(self):
        reg = PluginRegistry()
        reg.register("fake", _FakePlugin)
        assert reg.get("fake") is _FakePlugin

    def test_get_unknown_returns_none(self):
        reg = PluginRegistry()
        assert reg.get("nonexistent") is None

    def test_all_returns_all_plugins(self):
        reg = PluginRegistry()
        reg.register("a", _FakePlugin)
        reg.register("b", _FakePlugin)
        assert set(reg.all().keys()) == {"a", "b"}

    def test_load_entry_points_silent_on_missing_group(self):
        reg = PluginRegistry()
        reg.load_entry_points(group="ragkit.nonexistent_group")
        assert reg.all() == {}

    def test_load_entry_points_registers_valid_plugin(self):
        import importlib.metadata
        from unittest.mock import MagicMock, patch

        mock_ep = MagicMock()
        mock_ep.name = "myplugin"
        mock_ep.load.return_value = _FakePlugin

        with patch.object(importlib.metadata, "entry_points", return_value=[mock_ep]):
            reg = PluginRegistry()
            reg.load_entry_points(group="ragkit.plugins")

        assert reg.get("myplugin") is _FakePlugin

    def test_load_entry_points_skips_broken_plugin(self):
        import importlib.metadata
        from unittest.mock import MagicMock, patch

        mock_ep = MagicMock()
        mock_ep.name = "broken"
        mock_ep.load.side_effect = ImportError("missing dep")

        with patch.object(importlib.metadata, "entry_points", return_value=[mock_ep]):
            reg = PluginRegistry()
            reg.load_entry_points(group="ragkit.plugins")

        assert reg.get("broken") is None
