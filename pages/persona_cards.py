import html
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
CSV_PATH = DATA_DIR / "personas.csv"
EXPECTED_COLUMNS = [
    "name",
    "age",
    "occupation",
    "email",
    "phone",
    "address",
    "company",
    "traits",
    "goals",
    "pain_points",
    "behaviour",
]


def _coerce_list(value: Any) -> List[str]:
    """Normalize list-like persona values into a clean string list."""
    if value is None:
        return []

    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    else:
        items = [str(value)]

    cleaned_items = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned_items.append(text)

    return cleaned_items


def _normalize_persona(persona: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a persona dictionary with safe defaults for missing values."""
    if not isinstance(persona, dict):
        persona = {}

    return {
        "name": str(persona.get("name") or "Unknown").strip() or "Unknown",
        "age": str(persona.get("age") or "N/A").strip() or "N/A",
        "occupation": str(persona.get("occupation") or "Not provided").strip() or "Not provided",
        "email": str(persona.get("email") or "Not provided").strip() or "Not provided",
        "phone": str(persona.get("phone") or "Not provided").strip() or "Not provided",
        "address": str(persona.get("address") or "Not provided").strip() or "Not provided",
        "company": str(persona.get("company") or "Not provided").strip() or "Not provided",
        "traits": _coerce_list(persona.get("traits")),
        "goals": _coerce_list(persona.get("goals")),
        "pain_points": _coerce_list(persona.get("pain_points")),
        "behaviour": _coerce_list(persona.get("behaviour")),
    }


def _coerce_persona_input(personas: Optional[Any]) -> List[Dict[str, Any]]:
    """Normalize a persona payload from session state into a list of dictionaries."""
    if personas is None:
        return []

    if isinstance(personas, dict):
        return [personas]

    if isinstance(personas, list):
        return [persona for persona in personas if isinstance(persona, dict)]

    return []


def _get_personas_from_session() -> List[Dict[str, Any]]:
    """Read persona data from the session-state keys used by the current app."""
    for key in ("personas", "persona_cards", "persona"):
        value = st.session_state.get(key)
        if value is None:
            continue

        if isinstance(value, dict):
            return [value]
        if isinstance(value, list):
            return [persona for persona in value if isinstance(persona, dict)]

    return []


def _format_tag_list(values: List[str]) -> str:
    """Format list values for display inside the UI."""
    if not values:
        return "Not provided"
    return ", ".join(values)


def display_persona_card(persona: Optional[Dict[str, Any]]) -> None:
    """Render a single persona as a professional Streamlit card."""
    persona = _normalize_persona(persona)

    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #e2e8f0; border-radius:16px; padding:18px 20px; background:linear-gradient(135deg,#ffffff,#f8fafc); box-shadow:0 8px 24px rgba(15,23,42,0.06); margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:12px;">
                    <div>
                        <h4 style="margin:0 0 4px; color:#0f172a;">{html.escape(persona['name'])}</h4>
                        <p style="margin:0; color:#475569;">{html.escape(persona['occupation'])}</p>
                    </div>
                    <div style="background:#eff6ff; color:#1d4ed8; border-radius:999px; padding:6px 10px; font-size:0.85rem; font-weight:600;">Age {html.escape(str(persona['age']))}</div>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; color:#334155;">
                    <div><strong>Email:</strong> {html.escape(persona['email'])}</div>
                    <div><strong>Phone:</strong> {html.escape(persona['phone'])}</div>
                    <div><strong>Address:</strong> {html.escape(persona['address'])}</div>
                    <div><strong>Company:</strong> {html.escape(persona['company'])}</div>
                </div>
                <div style="margin-top:12px; color:#334155;">
                    <div style="margin-bottom:6px;"><strong>Traits:</strong> {html.escape(_format_tag_list(persona['traits']))}</div>
                    <div style="margin-bottom:6px;"><strong>Goals:</strong> {html.escape(_format_tag_list(persona['goals']))}</div>
                    <div style="margin-bottom:6px;"><strong>Pain Points:</strong> {html.escape(_format_tag_list(persona['pain_points']))}</div>
                    <div><strong>Behaviour:</strong> {html.escape(_format_tag_list(persona['behaviour']))}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_personas(personas: Optional[Any]) -> None:
    """Render a list of personas or a friendly empty state."""
    normalized_personas = [_normalize_persona(persona) for persona in _coerce_persona_input(personas)]

    if not normalized_personas:
        if isinstance(personas, str) and personas.strip():
            st.info("Structured persona data is not available yet. The page will render cards once another module provides a list of personas.")
        else:
            st.info("No personas are available yet. The page will display them once another module provides a persona list.")
        return

    for persona in normalized_personas:
        display_persona_card(persona)


def save_personas_to_csv(personas: Optional[Any]) -> Optional[Path]:
    """Export personas to CSV while preserving existing records and creating missing folders."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    normalized_personas = [_normalize_persona(persona) for persona in _coerce_persona_input(personas)]

    records: List[Dict[str, Any]] = []
    for persona in normalized_personas:
        records.append(
            {
                "name": persona["name"],
                "age": persona["age"],
                "occupation": persona["occupation"],
                "email": persona["email"],
                "phone": persona["phone"],
                "address": persona["address"],
                "company": persona["company"],
                "traits": ", ".join(persona["traits"]),
                "goals": ", ".join(persona["goals"]),
                "pain_points": ", ".join(persona["pain_points"]),
                "behaviour": ", ".join(persona["behaviour"]),
            }
        )

    try:
        new_df = pd.DataFrame(records, columns=EXPECTED_COLUMNS)

        if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
            existing_df = pd.read_csv(CSV_PATH)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
            combined_df = combined_df.reindex(columns=EXPECTED_COLUMNS)
            combined_df.to_csv(CSV_PATH, index=False)
        else:
            new_df.to_csv(CSV_PATH, index=False)

        return CSV_PATH
    except Exception as exc:
        st.error(f"Unable to export personas to CSV. Please try again. Detail: {exc}")
        return None


def main() -> None:
    """Render the persona cards page and export actions."""
    st.title("🧾 Persona Cards")
    st.caption("Review personas in a clean card layout and export them to CSV for downstream use.")

    personas = _get_personas_from_session()
    display_personas(personas)

    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Export to CSV", use_container_width=True):
            if not personas:
                st.info("There are no personas to export yet.")
            else:
                csv_path = save_personas_to_csv(personas)
                if csv_path is not None:
                    st.success(f"Personas exported successfully to {csv_path}.")

    with col2:
        st.caption("This page is designed to consume persona data from the existing app flow without generating new personas.")


if __name__ == "__main__":
    main()
