from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator

from ragkit.utils.logger import get_logger

logger = get_logger("ragkit.telemetry")


@dataclass
class Telemetry:
    indexing_time: float = 0.0
    query_latency: float = 0.0
    llm_cost_estimate: float = 0.0
    token_count: int = 0
    events: list[dict] = field(default_factory=list)

    def record(self, event: str, **kwargs) -> None:
        entry = {"event": event, **kwargs}
        self.events.append(entry)
        logger.info(event, **kwargs)

    def summary(self) -> dict:
        return {
            "indexing_time_s": round(self.indexing_time, 3),
            "query_latency_s": round(self.query_latency, 3),
            "llm_cost_estimate_usd": round(self.llm_cost_estimate, 6),
            "token_count": self.token_count,
        }


@contextmanager
def timer(label: str, telemetry: Telemetry | None = None) -> Generator[None, None, None]:
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if telemetry:
        telemetry.record(label, duration_s=round(elapsed, 3))
    else:
        logger.info(label, duration_s=round(elapsed, 3))
