from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List, Optional
from uuid import uuid4

import pandas as pd
import streamlit as st

PAGE_LINKS = [
    ("app.py", "Home / Workspace"),
    ("pages/research_copilot.py", "Research Copilot"),
    ("pages/persona_cards.py", "Persona Cards"),
    ("pages/survey.py", "Survey"),
    ("pages/interview.py", "Interview"),
    ("pages/focus_group.py", "Focus Group"),
    ("pages/insights.py", "Insights"),
    ("pages/action_center.py", "Action Center"),
    ("pages/product_strategy.py", "Product Strategy"),
    ("pages/experiment_simulator.py", "Experiment Simulator"),
    ("pages/dashboard.py", "Dashboard"),
    ("pages/reports.py", "Reports"),
]

RESEARCH_STAGES = [
    "Brief",
    "Personas",
    "Survey",
    "Interview",
    "Focus Group",
    "Insights",
    "Actions",
    "Decision",
]


def init_session_state() -> None:
    """Initialize the canonical single session-state contract used by every Streamlit page."""
    st.session_state.setdefault("personas", [])
    st.session_state.setdefault("experiment", {})
    st.session_state.setdefault("experiment_history", [])
    st.session_state.setdefault("survey_results", None)
    st.session_state.setdefault("persona_memories", {})
    st.session_state.setdefault("interview_results", [])
    st.session_state.setdefault("insights", None)
    st.session_state.setdefault("research_plan", None)
    st.session_state.setdefault("focus_group_results", [])
    st.session_state.setdefault("consultant_report", None)
    st.session_state.setdefault("product_actions", [])
    st.session_state.setdefault("state_version", 1)
    st.session_state.setdefault("toast_message", "")
    st.session_state.setdefault("experiment_signature", "")


def increment_state_version() -> int:
    st.session_state["state_version"] = st.session_state.get("state_version", 0) + 1
    return st.session_state["state_version"]


def get_state_version() -> int:
    return int(st.session_state.get("state_version", 1))


def apply_premium_theme() -> None:
    """Small shared design system; kept CSS-only so every existing page benefits."""
    st.markdown(
        """<style>
    :root { --ink:#e8edf8; --muted:#9aa8c1; --panel:rgba(17,25,45,.78); --accent:#7c8cff; }
    .stApp { background: radial-gradient(circle at 82% 0%, #202b58 0%, #0c1120 40%, #090d18 100%); color:var(--ink); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#111a31,#0a0f1d); border-right:1px solid #273250; }
    [data-testid="stSidebar"] .stPageLink a { border-radius:10px; padding:.45rem .6rem; transition:.18s ease; }
    [data-testid="stSidebar"] .stPageLink a:hover { background:#24315d; transform:translateX(2px); }
    div[data-testid="stMetric"] { background:var(--panel); border:1px solid #2a385d; border-radius:14px; padding:14px; }
    div[data-testid="stMetric"]:hover { border-color:#7184ff; transform:translateY(-2px); transition:.18s ease; }
    .stButton > button, .stDownloadButton > button { border-radius:10px; border:0; background:linear-gradient(135deg,#7282ff,#a164ff); color:white; font-weight:650; }
    .stButton > button:hover, .stDownloadButton > button:hover { filter:brightness(1.12); transform:translateY(-1px); }
    .research-hero { padding:1.35rem 1.5rem; border:1px solid #344779; border-radius:18px; background:linear-gradient(115deg,rgba(73,89,178,.40),rgba(21,29,54,.72)); margin-bottom:1rem; }
    .research-hero h1 { margin:0; font-size:2rem; } .research-hero p { color:var(--muted); margin:.35rem 0 0; }
    .timeline-container { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:1.2rem; }
    .timeline-pill { display:inline-flex; align-items:center; gap:6px; padding:6px 12px; border-radius:999px; font-size:12px; font-weight:600; border:1px solid #334155; background:rgba(30,41,59,0.7); color:#94a3b8; }
    .timeline-pill.completed { border-color:#10b981; background:rgba(16,185,129,0.12); color:#34d399; }
    .timeline-pill.current { border-color:#6366f1; background:rgba(99,102,241,0.22); color:#818cf8; box-shadow:0 0 12px rgba(99,102,241,0.3); }
    .timeline-state { opacity:.95; }
    .timeline-label { color:inherit; }
    .synthetic-badge { display:inline-block; font-size:11px; padding:3px 8px; border-radius:6px; background:#1e293b; color:#94a3b8; border:1px solid #475569; }
    </style>""",
        unsafe_allow_html=True,
    )


def render_synthetic_disclaimer() -> None:
    """Renders a mandatory audit and transparency disclaimer for synthetic research outputs."""
    st.caption(
        "Synthetic Data & AI Simulation Notice: All participant responses, quotes, and scores "
        "are generated through synthetic persona modeling for product discovery. Validate "
        "critical findings with real users prior to commercial launch."
    )


def get_personas() -> List[Dict[str, Any]]:
    personas = st.session_state.get("personas", [])
    if not isinstance(personas, list):
        return []
    return [dict(persona) for persona in personas if isinstance(persona, Mapping)]


def get_experiment() -> Dict[str, Any]:
    experiment = st.session_state.get("experiment", {})
    return dict(experiment) if isinstance(experiment, Mapping) else {}


def get_experiment_history() -> List[Dict[str, Any]]:
    history = st.session_state.get("experiment_history", [])
    if not isinstance(history, list):
        return []
    return [dict(item) for item in history if isinstance(item, Mapping)]


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
    st.session_state["focus_group_results"] = []
    st.session_state["consultant_report"] = None
    st.session_state["product_actions"] = []
    increment_state_version()


def save_experiment_snapshot(experiment: Mapping[str, Any], personas: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Store a lightweight experiment history record in session state."""
    now = datetime.now(timezone.utc).isoformat()
    payload = dict(experiment)
    payload.setdefault("experiment_id", str(uuid4()))
    payload.setdefault("created_at", now)
    payload["updated_at"] = now
    payload["persona_count_generated"] = len(personas or [])

    history = get_experiment_history()
    history = [item for item in history if item.get("experiment_id") != payload["experiment_id"]]
    history.insert(0, payload)
    st.session_state["experiment_history"] = history[:12]
    st.session_state["experiment"] = payload
    increment_state_version()
    return payload


def apply_professional_theme() -> None:
    """Apply a restrained visual layer over Streamlit's native components."""
    st.markdown(
        """
        <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --ink: #111827;
            --muted: #64748b;
            --surface: #ffffff;
            --panel: #f8fafc;
            --line: #e2e8f0;
            --success: #16a34a;
            --warning: #f59e0b;
        }
        .stApp {
            background:
                linear-gradient(180deg, #eef6ff 0, #ffffff 260px),
                #ffffff;
            color: var(--ink);
        }
        [data-testid="stSidebar"] {
            background: #0f172a;
            color: #e5e7eb;
        }
        [data-testid="stSidebar"] * {
            color: #e5e7eb;
        }
        [data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }
        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        div[data-testid="stForm"] {
            border-radius: 8px;
        }
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            font-weight: 600;
        }
        .stButton > button[kind="primary"] {
            background: var(--primary);
            border-color: var(--primary-dark);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(active_label: str) -> None:
    """Render consistent navigation and workflow status across all pages."""
    personas = get_personas()
    survey_results = get_survey_results()
    interview_results = get_interview_results()
    insights = get_insights()
    responses = survey_results.get("responses", []) if survey_results else []

    with st.sidebar:
        st.title("AI Research Studio")
        st.caption("From research brief to launch decision")
        for path, label in PAGE_LINKS:
            prefix = ">" if label == active_label else ""
            st.page_link(path, label=f"{prefix} {label}".strip())

        st.divider()
        st.metric("Personas", len(personas))
        st.metric("Survey responses", len(responses))
        st.metric("Interview messages", len(interview_results))
        st.metric("Focus group turns", len(st.session_state.get("focus_group_results", [])))

        if personas and responses and insights:
            st.success("Workflow complete")
        elif personas and responses:
            st.info("Survey complete")
        elif personas:
            st.info("Personas ready")
        else:
            st.warning("Start in Workspace")


def _state_get(key: str, default: Any = None) -> Any:
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default


def _has_payload(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, pd.DataFrame):
        return not value.empty
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set)):
        return len(value) > 0
    if isinstance(value, str):
        return bool(value.strip())
    try:
        return bool(value)
    except Exception:
        return False


def _normalized_stage(current_step: str) -> str:
    normalized = re.sub(r"\s+", " ", str(current_step or "").strip().lower())
    aliases = {
        "workspace": "Brief",
        "home": "Brief",
        "home / workspace": "Brief",
        "brief & setup": "Brief",
        "research copilot": "Brief",
        "persona": "Personas",
        "persona cards": "Personas",
        "interviews": "Interview",
        "interview mode": "Interview",
        "action center": "Actions",
        "product consultant": "Actions",
        "executive product strategy": "Actions",
        "dashboard": "Decision",
        "executive dashboard": "Decision",
        "executive research dashboard": "Decision",
    }
    if normalized in aliases:
        return aliases[normalized]
    for stage in RESEARCH_STAGES:
        if normalized == stage.lower():
            return stage
    return ""


def render_research_timeline(current_step: str = "") -> None:
    """Render the research lifecycle timeline from real session-state payloads only."""
    experiment = get_experiment()
    personas = get_personas()
    survey = get_survey_results()
    interviews = get_interview_results()
    focus_group = _state_get("focus_group_results", [])
    insights = get_insights()
    actions = _state_get("product_actions", [])
    decision = (
        _state_get("consultant_report")
        or _state_get("product_decision")
        or _state_get("product_decisions")
    )

    completed = {
        "Brief": _has_payload(experiment),
        "Personas": _has_payload(personas),
        "Survey": _has_payload(survey),
        "Interview": _has_payload(interviews),
        "Focus Group": _has_payload(focus_group),
        "Insights": _has_payload(insights),
        "Actions": _has_payload(actions),
        "Decision": _has_payload(decision),
    }
    active_stage = _normalized_stage(current_step)
    status_text = {
        "completed": "&#10003; completed",
        "current": "&#9679; current",
        "pending": "&#9675; pending",
    }

    pills_html = []
    for stage in RESEARCH_STAGES:
        status = "current" if stage == active_stage else "completed" if completed[stage] else "pending"
        pills_html.append(
            f'<span class="timeline-pill {status}">'
            f'<span class="timeline-state">{status_text[status]}</span>'
            f'<span class="timeline-label">{escape(stage)}</span>'
            "</span>"
        )

    st.markdown(
        '<div class="timeline-container">' + "".join(pills_html) + "</div>",
        unsafe_allow_html=True,
    )


def render_page_header(
    title: str,
    caption: str,
    active_stage: Optional[str] = None,
) -> None:
    apply_professional_theme()
    apply_premium_theme()
    st.markdown(
        f'<div class="research-hero"><h1>{escape(title)}</h1><p>{escape(caption)}</p></div>',
        unsafe_allow_html=True,
    )
    if active_stage:
        render_research_timeline(active_stage)

    message = st.session_state.pop("toast_message", "")
    if message:
        st.toast(message)


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
