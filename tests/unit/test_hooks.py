from ragkit.core.hooks import HookRegistry


def test_hook_fires():
    registry = HookRegistry()
    calls = []

    @registry.on("before_generate")
    def handler(prompt):
        calls.append(prompt)

    registry.fire("before_generate", "test prompt")
    assert calls == ["test prompt"]


def test_multiple_hooks_same_event():
    registry = HookRegistry()
    calls = []

    registry.register("event", lambda: calls.append(1))
    registry.register("event", lambda: calls.append(2))
    registry.fire("event")
    assert calls == [1, 2]


def test_clear_hooks():
    registry = HookRegistry()
    calls = []
    registry.register("event", lambda: calls.append(1))
    registry.clear("event")
    registry.fire("event")
    assert calls == []


def test_clear_all_hooks():
    registry = HookRegistry()
    calls = []
    registry.register("a", lambda: calls.append("a"))
    registry.register("b", lambda: calls.append("b"))
    registry.clear()
    registry.fire("a")
    registry.fire("b")
    assert calls == []
