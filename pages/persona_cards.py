import html
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

import pandas as pd
import streamlit as st

from models.persona import BigFivePersonality, Persona

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
CSV_PATH = DATA_DIR / "personas.csv"
EXPECTED_COLUMNS = [
    "id",
    "avatar_url",
    "name",
    "age",
    "gender",
    "occupation",
    "education",
    "income",
    "email",
    "phone",
    "address",
    "company",
    "goals",
    "pain_points",
    "traits",
    "behaviour",
    "technology_usage",
    "buying_behaviour",
    "psychological_profile",
    "behavior_pattern",
    "created_at",
    "updated_at",
    "big_five_openness",
    "big_five_conscientiousness",
    "big_five_extraversion",
    "big_five_agreeableness",
    "big_five_neuroticism",
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
    elif isinstance(value, dict):
        items = [f"{key}: {item}" for key, item in value.items() if item not in (None, "")]
    else:
        items = [str(value)]

    cleaned_items: List[str] = []
    for item in items:
        text = str(item).strip() if not isinstance(item, str) else item.strip()
        if text:
            cleaned_items.append(text)

    return cleaned_items


def _normalize_persona(persona: Optional[Any]) -> Persona:
    """Return a persona object with safe defaults for missing values."""
    if isinstance(persona, Persona):
        return persona

    if isinstance(persona, dict):
        return Persona.from_dict(persona)

    return Persona.from_dict({})


def _coerce_persona_input(personas: Optional[Any]) -> List[Persona]:
    """Normalize a persona payload from session state into a list of persona objects."""
    if personas is None:
        return []

    if isinstance(personas, dict):
        return [_normalize_persona(personas)]

    if isinstance(personas, list):
        return [_normalize_persona(persona) for persona in personas if isinstance(persona, dict) or isinstance(persona, Persona)]

    return []


def _get_personas_from_session() -> List[Persona]:
    """Read persona data from the session-state keys used by the current app."""
    for key in ("personas", "persona_cards", "persona"):
        value = st.session_state.get(key)
        if value is None:
            continue

        if isinstance(value, dict):
            return [_normalize_persona(value)]
        if isinstance(value, list):
            return [_normalize_persona(persona) for persona in value if isinstance(persona, dict) or isinstance(persona, Persona)]

    return []


def _format_text(value: Any, default: str = "Not provided") -> str:
    """Format nested dictionaries, lists, or strings for UI display."""
    if value is None:
        return default

    if isinstance(value, (list, tuple)):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(parts) if parts else default

    if isinstance(value, dict):
        parts = [f"{key}: {val}" for key, val in value.items() if str(val).strip()]
        return ", ".join(parts) if parts else default

    text = str(value).strip()
    return text or default


def _format_badges(values: Sequence[str], accent: str = "#eff6ff") -> str:
    """Render a compact badge list as HTML."""
    items = [item.strip() for item in values if str(item).strip()]
    if not items:
        return '<span style="color:#64748b;">Not provided</span>'

    badge_html = "".join(
        f'<span style="display:inline-block;padding:6px 10px;margin:4px 6px 4px 0;border-radius:999px;background:{accent};color:#0f172a;font-size:0.8rem;font-weight:600;">{html.escape(item)}</span>'
        for item in items[:10]
    )
    return f'<div>{badge_html}</div>'


def _build_avatar_url(persona: Persona) -> str:
    """Return an explicit avatar URL if provided, otherwise generate a fallback."""
    if persona.avatar_url and isinstance(persona.avatar_url, str) and persona.avatar_url.strip():
        return persona.avatar_url.strip()

    name = persona.name or "Unknown"
    return f"https://api.dicebear.com/9.x/initials/svg?seed={quote(name)}"


def _get_age_value(persona: Persona) -> Optional[int]:
    """Extract an integer age from legacy and new persona data."""
    if persona.age in (None, "", "N/A", "Not provided"):
        return None

    match = re.search(r"(\d+)", str(persona.age))
    if not match:
        return None

    return int(match.group(1))


def _filter_personas(personas: Sequence[Persona], search: str, gender: str, occupation: str, age_range: Tuple[int, int]) -> List[Persona]:
    """Filter personas dynamically by the provided controls."""
    search_query = search.strip().lower()
    min_age, max_age = age_range

    filtered: List[Persona] = []
    for persona in personas:
        if search_query and search_query not in persona.name.lower():
            continue

        if gender != "All" and persona.gender.lower() != gender.lower():
            continue

        if occupation != "All" and persona.occupation.lower() != occupation.lower():
            continue

        age_value = _get_age_value(persona)
        if age_value is not None and not (min_age <= age_value <= max_age):
            continue

        filtered.append(persona)

    return filtered


def _sort_personas(personas: Sequence[Persona], sort_by: str) -> List[Persona]:
    """Sort filtered personas using the selected frontend control."""
    if sort_by == "Age":
        return sorted(
            personas,
            key=lambda persona: (_get_age_value(persona) is None, _get_age_value(persona) or 0, persona.name.lower()),
        )

    if sort_by == "Occupation":
        return sorted(personas, key=lambda persona: (persona.occupation.lower(), persona.name.lower()))

    if sort_by == "Income":
        return sorted(personas, key=lambda persona: (str(persona.income).lower(), persona.name.lower()))

    return sorted(personas, key=lambda persona: persona.name.lower())


def _render_big_five(persona: Persona) -> str:
    """Render Big Five scores as a clean HTML-based progress visualization."""
    big_five = persona.big_five if isinstance(persona.big_five, BigFivePersonality) else BigFivePersonality.from_value(persona.big_five)
    traits = [
        ("Openness", big_five.openness),
        ("Conscientiousness", big_five.conscientiousness),
        ("Extraversion", big_five.extraversion),
        ("Agreeableness", big_five.agreeableness),
        ("Neuroticism", big_five.neuroticism),
    ]

    sections: List[str] = []
    for label, value in traits:
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = 0.0

        normalized = max(0.0, min(100.0, score))
        sections.append(
            f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px; color:#334155; font-size:0.9rem;">
                    <span>{html.escape(label)}</span>
                    <span>{int(normalized)}%</span>
                </div>
                <div style="height:8px; background:#e2e8f0; border-radius:999px; overflow:hidden;">
                    <div style="width:{normalized:.0f}%; height:100%; background:linear-gradient(90deg,#2563eb,#7c3aed); border-radius:999px;"></div>
                </div>
            </div>
            """
        )

    return "".join(sections)


def display_persona_card(persona: Optional[Any]) -> None:
    """Render a single persona as a polished Streamlit card."""
    persona_obj = _normalize_persona(persona)
    avatar_url = _build_avatar_url(persona_obj)

    with st.container():
        st.markdown(
            f"""
            <div style="border:1px solid #e2e8f0; border-radius:24px; padding:22px; background:linear-gradient(135deg,#ffffff,#f8fafc); box-shadow:0 18px 42px rgba(15,23,42,0.08); margin-bottom:18px;">
                <div style="display:flex; gap:18px; align-items:flex-start; flex-wrap:wrap;">
                    <div style="width:102px; height:102px; border-radius:50%; overflow:hidden; background:#eef2ff; display:flex; align-items:center; justify-content:center; box-shadow:0 10px 20px rgba(37,99,235,0.16); border:3px solid #dbeafe;">
                        <img src="{avatar_url}" alt="Avatar" style="width:100%; height:100%; object-fit:cover;" />
                    </div>
                    <div style="flex:1; min-width:260px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:10px;">
                            <div>
                                <h3 style="margin:0; color:#0f172a; font-size:1.45rem; font-weight:800;">{html.escape(persona_obj.name)}</h3>
                                <p style="margin:4px 0 0; color:#64748b; font-size:0.92rem; font-weight:600;">{html.escape(persona_obj.occupation)} • {html.escape(persona_obj.gender)} • {html.escape(persona_obj.age)}</p>
                            </div>
                            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                                <span style="display:inline-block;padding:7px 11px;border-radius:999px;background:#eff6ff;color:#1d4ed8;font-size:0.78rem;font-weight:800;">Age {html.escape(str(persona_obj.age))}</span>
                                <span style="display:inline-block;padding:7px 11px;border-radius:999px;background:#ecfdf5;color:#047857;font-size:0.78rem;font-weight:800;">{html.escape(persona_obj.income)}</span>
                                <span style="display:inline-block;padding:7px 11px;border-radius:999px;background:#fef3c7;color:#b45309;font-size:0.78rem;font-weight:800;">{html.escape(persona_obj.company)}</span>
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:8px; margin-bottom:14px;">
                            <div style="padding:10px 12px; border-radius:12px; background:#f8fafc; color:#334155; border:1px solid #e2e8f0;"><strong style="color:#0f172a;">Education:</strong> {html.escape(persona_obj.education)}</div>
                            <div style="padding:10px 12px; border-radius:12px; background:#f8fafc; color:#334155; border:1px solid #e2e8f0;"><strong style="color:#0f172a;">Email:</strong> {html.escape(persona_obj.email)}</div>
                            <div style="padding:10px 12px; border-radius:12px; background:#f8fafc; color:#334155; border:1px solid #e2e8f0;"><strong style="color:#0f172a;">Phone:</strong> {html.escape(persona_obj.phone)}</div>
                            <div style="padding:10px 12px; border-radius:12px; background:#f8fafc; color:#334155; border:1px solid #e2e8f0;"><strong style="color:#0f172a;">Address:</strong> {html.escape(persona_obj.address)}</div>
                        </div>

                        <div style="margin-bottom:14px;">
                            <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:6px;">Core Traits</div>
                            {_format_badges(persona_obj.traits, "#fef3c7")}
                        </div>

                        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; margin-bottom:14px;">
                            <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                                <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#2563eb; margin-bottom:6px;">Goals</div>
                                {_format_badges(persona_obj.goals, "#dcfce7")}
                            </div>
                            <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                                <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#dc2626; margin-bottom:6px;">Pain Points</div>
                                {_format_badges(persona_obj.pain_points, "#fee2e2")}
                            </div>
                        </div>

                        <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin-bottom:14px;">
                            <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                                <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#7c3aed; margin-bottom:6px;">Technology Usage</div>
                                <div style="color:#334155;">{html.escape(_format_text(persona_obj.technology_usage))}</div>
                            </div>
                            <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                                <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#0f766e; margin-bottom:6px;">Buying Behaviour</div>
                                <div style="color:#334155;">{html.escape(_format_text(persona_obj.buying_behaviour))}</div>
                            </div>
                            <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                                <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#b45309; margin-bottom:6px;">Psychological Profile</div>
                                <div style="color:#334155;">{html.escape(_format_text(persona_obj.psychological_profile))}</div>
                            </div>
                            <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                                <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#be185d; margin-bottom:6px;">Behavior Pattern</div>
                                <div style="color:#334155;">{html.escape(_format_text(persona_obj.behavior_pattern))}</div>
                            </div>
                        </div>

                        <div style="padding:12px; border-radius:14px; background:#f8fafc; border:1px solid #e2e8f0;">
                            <div style="font-size:0.78rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; color:#334155; margin-bottom:8px;">Big Five Personality</div>
                            {_render_big_five(persona_obj)}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def display_personas(personas: Optional[Any]) -> None:
    """Render a list of personas or a polished empty state."""
    normalized_personas = _coerce_persona_input(personas)

    if not normalized_personas:
        st.markdown(
            """
            <div style="border:1px dashed #cbd5e1; border-radius:20px; padding:28px; text-align:center; background:linear-gradient(135deg,#f8fafc,#ffffff);">
                <h3 style="margin:0 0 8px; color:#0f172a;">No personas generated yet</h3>
                <p style="margin:0; color:#64748b;">Create or load personas from the main workflow to populate this dashboard.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    search_col, gender_col, occupation_col, age_col = st.columns([1.8, 1, 1, 1.4])
    with search_col:
        search_query = st.text_input("Search by name", placeholder="Type a name to filter", key="persona_search")
    with gender_col:
        gender_options = ["All"] + sorted({persona.gender for persona in normalized_personas if persona.gender})
        selected_gender = st.selectbox("Gender", gender_options, key="persona_gender_filter")
    with occupation_col:
        occupation_options = ["All"] + sorted({persona.occupation for persona in normalized_personas if persona.occupation})
        selected_occupation = st.selectbox("Occupation", occupation_options, key="persona_occupation_filter")
    with age_col:
        available_ages = [age for age in (_get_age_value(persona) for persona in normalized_personas) if age is not None]
        if available_ages:
            age_range = st.slider("Age filter", min_value=min(available_ages), max_value=max(available_ages), value=(min(available_ages), max(available_ages)), key="persona_age_filter")
        else:
            age_range = st.slider("Age filter", min_value=0, max_value=100, value=(0, 100), key="persona_age_filter")

    sort_col, _ = st.columns([1, 3])
    with sort_col:
        sort_by = st.selectbox("Sort by", ["Name", "Age", "Occupation", "Income"], key="persona_sort_filter")

    filtered_personas = _filter_personas(normalized_personas, search_query, selected_gender, selected_occupation, age_range)
    sorted_personas = _sort_personas(filtered_personas, sort_by)

    st.caption(f"Showing {len(sorted_personas)} of {len(normalized_personas)} personas")

    if not sorted_personas:
        st.info("No personas match the current filters. Try broadening the search or changing the age range.")
        return

    for persona in sorted_personas:
        display_persona_card(persona)


def _flatten_persona(persona: Persona) -> Dict[str, Any]:
    """Convert a persona into a flat CSV-friendly record."""
    return {
        "id": persona.id,
        "avatar_url": persona.avatar_url,
        "name": persona.name,
        "age": persona.age,
        "gender": persona.gender,
        "occupation": persona.occupation,
        "education": persona.education,
        "income": persona.income,
        "email": persona.email,
        "phone": persona.phone,
        "address": persona.address,
        "company": persona.company,
        "goals": ", ".join(persona.goals),
        "pain_points": ", ".join(persona.pain_points),
        "traits": ", ".join(persona.traits),
        "behaviour": ", ".join(persona.behaviour),
        "technology_usage": persona.technology_usage,
        "buying_behaviour": persona.buying_behaviour,
        "psychological_profile": _format_text(persona.psychological_profile),
        "behavior_pattern": _format_text(persona.behavior_pattern),
        "created_at": persona.created_at,
        "updated_at": persona.updated_at,
        "big_five_openness": persona.big_five.openness,
        "big_five_conscientiousness": persona.big_five.conscientiousness,
        "big_five_extraversion": persona.big_five.extraversion,
        "big_five_agreeableness": persona.big_five.agreeableness,
        "big_five_neuroticism": persona.big_five.neuroticism,
    }


def _build_personas_dataframe(personas: Optional[Any]) -> pd.DataFrame:
    """Create a combined dataframe for saving and download."""
    normalized_personas = _coerce_persona_input(personas)
    records = [_flatten_persona(persona) for persona in normalized_personas]

    if not records:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    return pd.DataFrame(records)


def save_personas_to_csv(personas: Optional[Any]) -> Optional[Path]:
    """Export personas to CSV while preserving existing records and creating missing folders."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    new_df = _build_personas_dataframe(personas)

    try:
        if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
            existing_df = pd.read_csv(CSV_PATH)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
        else:
            combined_df = new_df

        combined_columns = [column for column in EXPECTED_COLUMNS if column in combined_df.columns]
        for column in combined_df.columns:
            if column not in combined_columns:
                combined_columns.append(column)

        combined_df = combined_df.reindex(columns=combined_columns)
        combined_df.to_csv(CSV_PATH, index=False)
        return CSV_PATH
    except Exception as exc:
        st.error(f"Unable to export personas to CSV. Please try again. Detail: {exc}")
        return None


def build_csv_bytes(personas: Optional[Any]) -> bytes:
    """Prepare a CSV payload for the Streamlit download button."""
    dataframe = _build_personas_dataframe(personas)
    dataframe = dataframe.reindex(columns=EXPECTED_COLUMNS, fill_value="")
    return dataframe.to_csv(index=False).encode("utf-8")


def main() -> None:
    """Render the persona cards page and export actions."""
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.2rem; }
        .stButton > button {
            border-radius: 14px;
            height: 2.9rem;
            font-weight: 700;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.16);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("🧾 Persona Cards")
    st.caption("Review personas in a polished dashboard, filter them instantly, and export the full dataset for downstream use.")

    personas = _get_personas_from_session()
    display_personas(personas)

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Export to CSV", use_container_width=True):
            if not personas:
                st.info("There are no personas to export yet.")
            else:
                csv_path = save_personas_to_csv(personas)
                if csv_path is not None:
                    st.success(f"Personas exported successfully to {csv_path}.")

    with col2:
        if personas:
            st.download_button(
                label="Download personas.csv",
                data=build_csv_bytes(personas),
                file_name="personas.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.caption("Download becomes available once personas have been generated or loaded.")


if __name__ == "__main__":
    main()
