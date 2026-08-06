from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st


PAGE_LINKS = [
    ("app.py", "Home / Workspace"),
    ("pages/persona_cards.py", "Persona Cards"),
    ("pages/survey.py", "Survey"),
    ("pages/interview.py", "Interview"),
    ("pages/insights.py", "Insights"),
    ("pages/dashboard.py", "Dashboard"),
]


def init_session_state() -> None:
    """Initialize the single session-state contract used by every Streamlit page."""
    st.session_state.setdefault("personas", [])
    st.session_state.setdefault("experiment", {})
    st.session_state.setdefault("survey_results", None)
    st.session_state.setdefault("persona_memories", {})
    st.session_state.setdefault("interview_results", [])
    st.session_state.setdefault("insights", None)


def get_personas() -> List[Dict[str, Any]]:
    personas = st.session_state.get("personas", [])
    if not isinstance(personas, list):
        return []
    return [dict(persona) for persona in personas if isinstance(persona, Mapping)]


def get_experiment() -> Dict[str, Any]:
    experiment = st.session_state.get("experiment", {})
    return dict(experiment) if isinstance(experiment, Mapping) else {}


def get_survey_results() -> Optional[Dict[str, Any]]:
    survey_results = st.session_state.get("survey_results")
    return dict(survey_results) if isinstance(survey_results, Mapping) else None


def get_interview_results() -> List[Dict[str, Any]]:
    rows = st.session_state.get("interview_results", [])
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def get_insights() -> Optional[Dict[str, Any]]:
    insights = st.session_state.get("insights")
    return dict(insights) if isinstance(insights, Mapping) else None


def save_personas(personas: List[Dict[str, Any]]) -> None:
    st.session_state["personas"] = personas
    st.session_state["survey_results"] = None
    st.session_state["persona_memories"] = {}
    st.session_state["interview_results"] = []
    st.session_state["insights"] = None


def render_sidebar(active_label: str) -> None:
    """Render consistent navigation and workflow status across all pages."""
    personas = get_personas()
    survey_results = get_survey_results()
    interview_results = get_interview_results()
    insights = get_insights()
    responses = survey_results.get("responses", []) if survey_results else []

    with st.sidebar:
        st.title("Synthetic Users")
        st.caption("Workspace -> Personas -> Survey -> Interview -> Insights -> Dashboard")
        for path, label in PAGE_LINKS:
            prefix = ">" if label == active_label else ""
            st.page_link(path, label=f"{prefix} {label}".strip())

        st.divider()
        st.metric("Personas", len(personas))
        st.metric("Survey responses", len(responses))
        st.metric("Interview messages", len(interview_results))

        if personas and responses and insights:
            st.success("Workflow complete")
        elif personas and responses:
            st.info("Survey complete")
        elif personas:
            st.info("Personas ready")
        else:
            st.warning("Start in Workspace")


def render_page_header(title: str, caption: str) -> None:
    st.title(title)
    st.caption(caption)


def as_text(value: Any, default: str = "Not provided") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip() or default
    if isinstance(value, Mapping):
        return ", ".join(f"{key}: {item}" for key, item in value.items() if str(item).strip()) or default
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
        return ", ".join(str(item).strip() for item in value if str(item).strip()) or default
    return str(value).strip() or default


def as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, Mapping):
        return [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def age_number(value: Any) -> Optional[int]:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None


def persona_value(persona: Mapping[str, Any], key: str, default: Any = "") -> Any:
    aliases = {
        "buying_behavior": ["buying_behavior", "buying_behaviour"],
        "big_five_personality": ["big_five_personality", "big_five", "big_five_scores"],
    }
    for candidate in aliases.get(key, [key]):
        if candidate in persona and persona[candidate] not in (None, ""):
            return persona[candidate]
    return default


def flatten_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    flattened: Dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, (dict, list, tuple)):
            flattened[key] = json.dumps(value, ensure_ascii=False)
        else:
            flattened[key] = value
    return flattened


def records_to_dataframe(records: List[Mapping[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame([flatten_record(record) for record in records])


def require_personas() -> Optional[List[Dict[str, Any]]]:
    personas = get_personas()
    if personas:
        return personas

    st.warning("No personas are available. Generate personas in the workspace first.")
    st.page_link("app.py", label="Go to Workspace")
    return None
