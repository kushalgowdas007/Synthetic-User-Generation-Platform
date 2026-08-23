from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from services.telemetry import telemetry


def _normalize_str(val: Any) -> str:
    return str(val or "").strip().lower()


def compute_experiment_signature(experiment: Mapping[str, Any]) -> str:
    """Deterministic SHA-256 signature for experiment configuration."""
    normalized = {
        "product_name": _normalize_str(experiment.get("product_name")),
        "description": _normalize_str(experiment.get("description")),
        "target_audience": _normalize_str(experiment.get("target_audience")),
        "research_objective": _normalize_str(experiment.get("research_objective") or experiment.get("research_goal")),
        "industry": _normalize_str(experiment.get("industry")),
        "simulation_type": _normalize_str(experiment.get("simulation_type")),
        "persona_count": int(experiment.get("persona_count", 3) or 3),
        "age": _normalize_str(experiment.get("age")),
        "gender": _normalize_str(experiment.get("gender")),
        "profession": _normalize_str(experiment.get("profession")),
        "location": _normalize_str(experiment.get("location")),
        "interests": _normalize_str(experiment.get("interests")),
    }
    encoded = json.dumps(normalized, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_survey_signature(
    experiment_sig: str,
    personas: Sequence[Mapping[str, Any]],
    questions: Sequence[Mapping[str, Any]],
    product: str,
    objective: str,
) -> str:
    """Deterministic SHA-256 signature for survey template and inputs."""
    persona_keys = sorted([str(p.get("id") or p.get("name", "")) for p in personas])
    question_keys = [str(q.get("id") or q.get("question", "")) for q in questions]
    normalized = {
        "experiment_sig": experiment_sig,
        "personas": persona_keys,
        "questions": question_keys,
        "product": _normalize_str(product),
        "objective": _normalize_str(objective),
    }
    encoded = json.dumps(normalized, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_insight_signature(
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    focus_rows: Sequence[Mapping[str, Any]],
    personas: Sequence[Mapping[str, Any]],
) -> str:
    """Deterministic SHA-256 signature for insight input data."""
    survey_digest = ""
    if survey_results:
        responses = survey_results.get("responses", [])
        survey_digest = f"responses:{len(responses)}:fit:{survey_results.get('product_fit_score', 0)}"
    interview_digest = f"int:{len(interview_rows)}:msg:{sum(len(str(r.get('message', ''))) for r in interview_rows)}"
    focus_digest = f"focus:{len(focus_rows)}:msg:{sum(len(str(r.get('message', ''))) for r in focus_rows)}"
    persona_digest = f"personas:{len(personas)}:{','.join(str(p.get('name', '')) for p in personas)}"
    
    combined = f"{survey_digest}|{interview_digest}|{focus_digest}|{persona_digest}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_report_signature(
    experiment_sig: str,
    insight_sig: str,
    has_consultant_report: bool,
    persona_count: int,
) -> str:
    """Deterministic SHA-256 signature for generated PDF reports."""
    combined = f"exp:{experiment_sig}|ins:{insight_sig}|consultant:{has_consultant_report}|p_count:{persona_count}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


class BoundedLRUCache:
    """Lightweight in-memory LRU cache with a maximum capacity."""

    def __init__(self, capacity: int = 50, name: str = "cache") -> None:
        self._capacity = capacity
        self._name = name
        self._store: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if not key:
            return None
        if key in self._store:
            self._store.move_to_end(key)
            telemetry.record_cache_hit(self._name)
            return self._store[key]
        telemetry.record_cache_miss(self._name)
        return None

    def set(self, key: str, value: Any) -> None:
        if not key:
            return
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._capacity:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)


# Global bounded caches
persona_cache = BoundedLRUCache(capacity=30, name="persona_generation")
survey_cache = BoundedLRUCache(capacity=30, name="survey_execution")
insight_cache = BoundedLRUCache(capacity=30, name="insight_clustering")
report_cache = BoundedLRUCache(capacity=20, name="report_generation")
dashboard_cache = BoundedLRUCache(capacity=30, name="dashboard_aggregation")
