"""Small, local persistence layer for workspace save/load and experiment history.

The Streamlit UI remains session-first.  This store only provides an explicit
user action for preserving a demo/research workspace between browser sessions.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "workspace_history.json"


def _read() -> List[Dict[str, Any]]:
    try:
        value = json.loads(STORE_PATH.read_text(encoding="utf-8"))
        return [dict(item) for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def list_workspaces() -> List[Dict[str, Any]]:
    """Return newest saved workspaces first, without exposing mutable state."""
    return sorted(_read(), key=lambda item: str(item.get("saved_at", "")), reverse=True)


def save_workspace(
    *, experiment: Mapping[str, Any], personas: List[Mapping[str, Any]], survey_results: Mapping[str, Any] | None,
    interview_results: List[Mapping[str, Any]], insights: Mapping[str, Any] | None, persona_memories: Mapping[str, Any] | None = None,
    research_plan: Mapping[str, Any] | None = None, focus_group_results: List[Mapping[str, Any]] | None = None,
    consultant_report: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    if not experiment.get("experiment_name"):
        raise ValueError("An experiment name is required before saving a workspace.")
    record = {
        "id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f"),
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "experiment": dict(experiment),
        "personas": [dict(persona) for persona in personas],
        "survey_results": dict(survey_results or {}),
        "interview_results": [dict(item) for item in interview_results],
        "insights": dict(insights or {}),
        "persona_memories": dict(persona_memories or {}),
        "research_plan": dict(research_plan or {}),
        "focus_group_results": [dict(item) for item in (focus_group_results or [])],
        "consultant_report": dict(consultant_report or {}),
    }
    records = [item for item in _read() if item.get("experiment", {}).get("experiment_name") != experiment.get("experiment_name")]
    records.append(record)
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return record


def load_workspace(workspace_id: str) -> Dict[str, Any] | None:
    for record in _read():
        if record.get("id") == workspace_id:
            return record
    return None
