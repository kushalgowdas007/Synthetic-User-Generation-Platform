from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Mapping, Optional, Sequence

import streamlit as st

from services.telemetry import telemetry

logger = logging.getLogger(__name__)

_PERFORMANCE_LOGS: List[Dict[str, Any]] = []


def _normalize_str(value: Any) -> str:
    return str(value or "").strip().lower()


def _json_signature(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    return _json_signature(normalized)


def compute_survey_signature(*args: Any, **kwargs: Any) -> str:
    """Deterministic signature for survey template and inputs.

    Supports both historical call styles:
    compute_survey_signature(experiment_sig, personas, questions, product, objective)
    compute_survey_signature(personas, questions, product, objective)
    """
    experiment_sig = str(kwargs.get("experiment_sig", ""))
    personas: Sequence[Mapping[str, Any]]
    questions: Sequence[Mapping[str, Any]]
    product: str
    objective: str

    if len(args) >= 5 and isinstance(args[0], str):
        experiment_sig = args[0]
        personas = args[1]
        questions = args[2]
        product = str(args[3])
        objective = str(args[4])
    elif len(args) >= 4:
        personas = args[0]
        questions = args[1]
        product = str(args[2])
        objective = str(args[3])
    else:
        personas = kwargs.get("personas", [])
        questions = kwargs.get("questions", kwargs.get("survey_questions", []))
        product = str(kwargs.get("product", kwargs.get("product_name", "")))
        objective = str(kwargs.get("objective", kwargs.get("research_goal", "")))

    payload = {
        "experiment_sig": experiment_sig,
        "personas": sorted(str(p.get("id") or p.get("name", "")) for p in personas if isinstance(p, Mapping)),
        "questions": [str(q.get("id") or q.get("question", "")) for q in questions if isinstance(q, Mapping)],
        "product": _normalize_str(product),
        "objective": _normalize_str(objective),
    }
    return _json_signature(payload)


def compute_insight_signature(
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    focus_rows: Sequence[Mapping[str, Any]],
    personas: Sequence[Mapping[str, Any]] | Sequence[str],
) -> str:
    """Deterministic SHA-256 signature for insight input data."""
    persona_keys = [
        str(item.get("id") or item.get("name", ""))
        if isinstance(item, Mapping)
        else str(item)
        for item in personas
    ]
    payload = {
        "survey_results": survey_results or {},
        "interview_rows": list(interview_rows),
        "focus_rows": list(focus_rows),
        "personas": sorted(persona_keys),
    }
    return _json_signature(payload)


def compute_report_signature(*args: Any, **kwargs: Any) -> str:
    """Deterministic signature for generated research reports.

    Supports both:
    compute_report_signature(experiment_sig=..., insight_sig=..., has_consultant_report=..., persona_count=...)
    compute_report_signature(experiment, personas, survey_results, insights)
    """
    if kwargs:
        payload = {
            "experiment_sig": str(kwargs.get("experiment_sig", "")),
            "insight_sig": str(kwargs.get("insight_sig", "")),
            "has_consultant_report": bool(kwargs.get("has_consultant_report", False)),
            "persona_count": int(kwargs.get("persona_count", 0) or 0),
        }
        return _json_signature(payload)

    if len(args) >= 4 and isinstance(args[0], Mapping):
        experiment, personas, survey_results, insights = args[:4]
        payload = {
            "experiment_sig": compute_experiment_signature(experiment),
            "personas": [
                str(p.get("id") or p.get("name", ""))
                for p in personas
                if isinstance(p, Mapping)
            ],
            "survey_results": survey_results or {},
            "insight_score": (insights or {}).get("confidence_score", 0) if isinstance(insights, Mapping) else 0,
            "product_fit_score": (insights or {}).get("product_fit_score", 0) if isinstance(insights, Mapping) else 0,
        }
        return _json_signature(payload)

    experiment_sig = str(args[0]) if len(args) > 0 else ""
    insight_sig = str(args[1]) if len(args) > 1 else ""
    has_consultant_report = bool(args[2]) if len(args) > 2 else False
    persona_count = int(args[3] or 0) if len(args) > 3 else 0
    return _json_signature(
        {
            "experiment_sig": experiment_sig,
            "insight_sig": insight_sig,
            "has_consultant_report": has_consultant_report,
            "persona_count": persona_count,
        }
    )


def record_performance_metric(
    operation: str,
    duration_sec: float,
    cache_hit: bool,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    entry = {
        "operation": operation,
        "duration_sec": round(duration_sec, 3),
        "cache_hit": cache_hit,
        "timestamp": time.time(),
        "metadata": metadata or {},
    }
    _PERFORMANCE_LOGS.append(entry)
    if len(_PERFORMANCE_LOGS) > 100:
        _PERFORMANCE_LOGS.pop(0)
    logger.info("Performance telemetry: %s", entry)


def get_performance_metrics() -> List[Dict[str, Any]]:
    return list(_PERFORMANCE_LOGS)


def clear_performance_metrics() -> None:
    _PERFORMANCE_LOGS.clear()


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


@st.cache_data(show_spinner=False, ttl=3600)
def cached_survey_analytics(responses_json: str, template_name: str) -> Dict[str, Any]:
    """Cache deterministic survey analytics computation."""
    from backend.services.survey_service import calculate_survey_analytics

    responses = json.loads(responses_json)
    return calculate_survey_analytics(responses)


@st.cache_data(show_spinner=False, ttl=3600)
def cached_dashboard_aggregation(persona_rows_json: str, survey_results_json: str) -> Dict[str, Any]:
    """Precompute dashboard analytics metrics."""
    personas = json.loads(persona_rows_json)
    survey_results = json.loads(survey_results_json) if survey_results_json else None

    total_personas = len(personas)
    gender_counts: Dict[str, int] = {}
    occupation_counts: Dict[str, int] = {}
    tech_counts: Dict[str, int] = {}
    ages: List[float] = []

    for persona in personas:
        if not isinstance(persona, Mapping):
            continue
        gender = str(persona.get("gender", "Other")).title()
        gender_counts[gender] = gender_counts.get(gender, 0) + 1

        occupation = str(persona.get("occupation", "Other")).title()
        occupation_counts[occupation] = occupation_counts.get(occupation, 0) + 1

        tech = str(persona.get("technology_usage", "Medium")).title()
        tech_counts[tech] = tech_counts.get(tech, 0) + 1

        try:
            ages.append(float(str(persona.get("age", "")).split("-")[0]))
        except (TypeError, ValueError):
            pass

    avg_quality = sum(float(p.get("quality_score", 80)) for p in personas if isinstance(p, Mapping)) / max(1, total_personas)
    response_count = len((survey_results or {}).get("responses", [])) if isinstance(survey_results, Mapping) else 0

    return {
        "total_personas": total_personas,
        "average_age": round(sum(ages) / max(1, len(ages)), 1),
        "gender_counts": gender_counts,
        "occupation_counts": occupation_counts,
        "technology_counts": tech_counts,
        "average_quality_score": round(avg_quality, 1),
        "survey_response_count": response_count,
    }


persona_cache = BoundedLRUCache(capacity=30, name="persona_generation")
survey_cache = BoundedLRUCache(capacity=30, name="survey_execution")
insight_cache = BoundedLRUCache(capacity=30, name="insight_clustering")
report_cache = BoundedLRUCache(capacity=20, name="report_generation")
dashboard_cache = BoundedLRUCache(capacity=30, name="dashboard_aggregation")
