from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

HookFn = Callable[..., Any]


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, list[HookFn]] = defaultdict(list)

    def on(self, event: str) -> Callable[[HookFn], HookFn]:
        def decorator(fn: HookFn) -> HookFn:
            self._hooks[event].append(fn)
            return fn
        return decorator

    def register(self, event: str, fn: HookFn) -> None:
        self._hooks[event].append(fn)

    def fire(self, event: str, *args: Any, **kwargs: Any) -> None:
        for fn in self._hooks.get(event, []):
            fn(*args, **kwargs)

    def clear(self, event: str | None = None) -> None:
        if event:
            self._hooks.pop(event, None)
        else:
            self._hooks.clear()
