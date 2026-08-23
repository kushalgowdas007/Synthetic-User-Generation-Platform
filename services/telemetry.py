from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger("ai_research_studio.telemetry")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class TelemetryTracker:
    """In-memory telemetry tracker for performance metrics, latencies, and cache stats."""

    def __init__(self) -> None:
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._cache_stats: Dict[str, int] = {"hits": 0, "misses": 0}
        self._api_calls: Dict[str, int] = defaultdict(int)
        self._retries: Dict[str, int] = defaultdict(int)
        self._errors: List[Dict[str, Any]] = []

    def record_latency(self, stage: str, duration_seconds: float) -> None:
        self._latencies[stage].append(round(duration_seconds, 3))
        logger.info("Stage '%s' completed in %.3fs", stage, duration_seconds)

    def record_cache_hit(self, cache_name: str) -> None:
        self._cache_stats["hits"] += 1
        logger.info("Cache HIT for '%s'", cache_name)

    def record_cache_miss(self, cache_name: str) -> None:
        self._cache_stats["misses"] += 1
        logger.info("Cache MISS for '%s'", cache_name)

    def record_api_call(self, provider: str = "gemini") -> None:
        self._api_calls[provider] += 1
        logger.info("API call dispatched to provider: %s", provider)

    def record_retry(self, operation: str, attempt: int) -> None:
        self._retries[operation] += 1
        logger.warning("Retry attempt %d for operation: %s", attempt, operation)

    def record_error(self, operation: str, error_message: str) -> None:
        self._errors.append({"operation": operation, "error": error_message, "timestamp": time.time()})
        logger.error("Error in %s: %s", operation, error_message)

    def get_summary(self) -> Dict[str, Any]:
        latest_latencies = {stage: (values[-1] if values else 0.0) for stage, values in self._latencies.items()}
        avg_latencies = {stage: round(sum(values) / max(1, len(values)), 3) for stage, values in self._latencies.items()}
        return {
            "latest_latencies_seconds": latest_latencies,
            "avg_latencies_seconds": avg_latencies,
            "cache_stats": dict(self._cache_stats),
            "api_calls": dict(self._api_calls),
            "retries": dict(self._retries),
            "error_count": len(self._errors),
        }

    def clear(self) -> None:
        self._latencies.clear()
        self._cache_stats = {"hits": 0, "misses": 0}
        self._api_calls.clear()
        self._retries.clear()
        self._errors.clear()


# Global telemetry singleton
telemetry = TelemetryTracker()


@contextmanager
def time_stage(stage_name: str) -> Generator[Dict[str, Any], None, None]:
    """Context manager to measure and log execution duration for a stage."""
    start_time = time.perf_counter()
    ctx: Dict[str, Any] = {"stage": stage_name, "duration": 0.0}
    try:
        yield ctx
    finally:
        duration = time.perf_counter() - start_time
        ctx["duration"] = round(duration, 3)
        telemetry.record_latency(stage_name, duration)
