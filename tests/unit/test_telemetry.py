from __future__ import annotations

import time

from ragkit.utils.telemetry import Telemetry, timer


class TestTelemetry:
    def test_record_stores_event(self):
        t = Telemetry()
        t.record("test_event", key="value")
        assert len(t.events) == 1
        assert t.events[0]["event"] == "test_event"
        assert t.events[0]["key"] == "value"

    def test_summary_fields(self):
        t = Telemetry()
        t.indexing_time = 1.5
        t.query_latency = 0.2
        t.llm_cost_estimate = 0.00042
        t.token_count = 500
        s = t.summary()
        assert s["indexing_time_s"] == 1.5
        assert s["query_latency_s"] == 0.2
        assert s["llm_cost_estimate_usd"] == 0.00042
        assert s["token_count"] == 500


class TestTimer:
    def test_timer_records_to_telemetry(self):
        t = Telemetry()
        with timer("my_label", t):
            pass
        assert len(t.events) == 1
        assert t.events[0]["event"] == "my_label"
        assert "duration_s" in t.events[0]

    def test_timer_without_telemetry_does_not_raise(self):
        with timer("no_telemetry"):
            pass

    def test_timer_measures_elapsed_time(self):
        t = Telemetry()
        with timer("sleep_test", t):
            time.sleep(0.05)
        assert t.events[0]["duration_s"] >= 0.04
