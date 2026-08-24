from __future__ import annotations

import hashlib
import json
<<<<<<< HEAD
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
=======
import logging
import time
from typing import Any, Dict, List, Mapping, Optional, Tuple

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# In-memory telemetry log for developer performance section
_PERFORMANCE_LOGS: List[Dict[str, Any]] = []


def record_performance_metric(operation: str, duration_sec: float, cache_hit: bool, metadata: Optional[Dict[str, Any]] = None) -> None:
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
    logger.info("Performance Telemetry: %s", entry)


def get_performance_metrics() -> List[Dict[str, Any]]:
    return list(_PERFORMANCE_LOGS)


def clear_performance_metrics() -> None:
    _PERFORMANCE_LOGS.clear()


# ------------------------------------------------------------
# SIGNATURE COMPUTATION
# ------------------------------------------------------------

def compute_experiment_signature(payload: Mapping[str, Any]) -> str:
    """Deterministic hash signature for experiment inputs."""
    normalized = {
        "product_name": str(payload.get("product_name", "")).strip().lower(),
        "target_audience": str(payload.get("target_audience", "")).strip().lower(),
        "age": str(payload.get("age", "")).strip().lower(),
        "gender": str(payload.get("gender", "")).strip().lower(),
        "profession": str(payload.get("profession", "")).strip().lower(),
        "location": str(payload.get("location", "")).strip().lower(),
        "interests": str(payload.get("interests", "")).strip().lower(),
        "persona_count": int(payload.get("persona_count", 1) or 1),
        "simulation_type": str(payload.get("simulation_type", "")).strip().lower(),
        "industry": str(payload.get("industry", "")).strip().lower(),
        "description": str(payload.get("description", "")).strip().lower(),
        "research_objective": str(payload.get("research_objective", "")).strip().lower(),
    }
    raw_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_survey_signature(personas: Sequence[Mapping[str, Any]], survey_questions: Sequence[Mapping[str, Any]], product_name: str, research_goal: str) -> str:
    """Deterministic hash signature for survey inputs."""
    persona_ids = sorted([str(p.get("id") or p.get("name", "")) for p in personas])
    q_ids = sorted([str(q.get("id") or q.get("question", "")) for q in survey_questions])
    normalized = {
        "persona_ids": persona_ids,
        "q_ids": q_ids,
        "product_name": str(product_name).strip().lower(),
        "research_goal": str(research_goal).strip().lower(),
    }
    raw_str = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()


def compute_insight_signature(survey_results: Optional[Mapping[str, Any]], interview_results: Sequence[Mapping[str, Any]], focus_group_results: Sequence[Mapping[str, Any]], persona_ids: Sequence[str]) -> str:
    """Deterministic hash signature for insight inputs."""
    s_hash = hashlib.md5(json.dumps(survey_results or {}, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    i_hash = hashlib.md5(json.dumps(list(interview_results), sort_keys=True, default=str).encode("utf-8")).hexdigest()
    f_hash = hashlib.md5(json.dumps(list(focus_group_results), sort_keys=True, default=str).encode("utf-8")).hexdigest()
    p_hash = hashlib.md5(json.dumps(sorted(persona_ids)).encode("utf-8")).hexdigest()
    combined = f"{s_hash}:{i_hash}:{f_hash}:{p_hash}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def compute_report_signature(experiment: Mapping[str, Any], personas: Sequence[Mapping[str, Any]], survey_results: Optional[Mapping[str, Any]], insights: Optional[Mapping[str, Any]]) -> str:
    """Deterministic hash signature for report generation."""
    e_sig = compute_experiment_signature(experiment)
    p_count = len(personas)
    s_fit = (survey_results or {}).get("product_fit_score", 0)
    i_score = (insights or {}).get("confidence_score", 0)
    combined = f"{e_sig}:{p_count}:{s_fit}:{i_score}"
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ------------------------------------------------------------
# STREAMLIT CACHED COMPUTATIONS
# ------------------------------------------------------------

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
    avg_age = sum(float(p.get("age", 30)) for p in personas) / max(1, total_personas)
    
    # Demographics
    gender_counts: Dict[str, int] = {}
    occupation_counts: Dict[str, int] = {}
    tech_counts: Dict[str, int] = {}
    
    for p in personas:
        g = str(p.get("gender", "Other")).title()
        gender_counts[g] = gender_counts.get(g, 0) + 1
        
        occ = str(p.get("occupation", "Other")).title()
        occupation_counts[occ] = occupation_counts.get(occ, 0) + 1
        
        tech = str(p.get("technology_usage", "Medium")).title()
        tech_counts[tech] = tech_counts.get(tech, 0) + 1
        
    avg_quality = sum(float(p.get("quality_score", 80)) for p in personas) / max(1, total_personas)
    
    return {
        "total_personas": total_personas,
        "average_age": round(avg_age, 1),
        "gender_counts": gender_counts,
        "occupation_counts": occupation_counts,
        "technology_counts": tech_counts,
        "average_quality_score": round(avg_quality, 1),
    }
>>>>>>> f68520b (Save local changes)
