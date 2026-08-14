from __future__ import annotations

import json
from collections.abc import Mapping
from urllib.parse import quote

import streamlit as st

from frontend.shared import (
    age_number,
    as_list,
    as_text,
    get_personas,
    init_session_state,
    persona_value,
    records_to_dataframe,
    render_page_header,
    render_sidebar,
    require_personas,
)


def avatar_url(persona: Mapping[str, object]) -> str:
    existing = str(persona.get("avatar_url", "")).strip()
    if existing:
        return existing
    return f"https://api.dicebear.com/9.x/initials/svg?seed={quote(as_text(persona.get('name'), 'Persona'))}"


def filtered_personas(personas: list[dict]) -> list[dict]:
    search_col, gender_col, occupation_col, sort_col = st.columns([1.6, 1, 1, 1])
    with search_col:
        search = st.text_input("Search", placeholder="Name, occupation, goal, or pain point")
    with gender_col:
        gender_options = ["All"] + sorted({as_text(persona.get("gender")) for persona in personas if persona.get("gender")})
        gender = st.selectbox("Gender", gender_options)
    with occupation_col:
        occupation_options = ["All"] + sorted({as_text(persona.get("occupation")) for persona in personas if persona.get("occupation")})
        occupation = st.selectbox("Occupation", occupation_options)
    with sort_col:
        sort_by = st.selectbox("Sort", ["Name", "Age", "Gender", "Occupation", "Income"])

    search_text = search.strip().lower()
    results: list[dict] = []
    for persona in personas:
        searchable_text = " ".join(
            [
                as_text(persona.get("name"), ""),
                as_text(persona.get("occupation"), ""),
                as_text(persona.get("bio"), ""),
                as_text(persona.get("goals"), ""),
                as_text(persona.get("pain_points"), ""),
                as_text(persona.get("technology_usage"), ""),
                as_text(persona_value(persona, "buying_behavior"), ""),
            ]
        ).lower()
        if search_text and search_text not in searchable_text:
            continue
        if gender != "All" and as_text(persona.get("gender")).lower() != gender.lower():
            continue
        if occupation != "All" and as_text(persona.get("occupation")).lower() != occupation.lower():
            continue
        results.append(persona)

    if sort_by == "Age":
        return sorted(results, key=lambda item: (age_number(item.get("age")) is None, age_number(item.get("age")) or 0, as_text(item.get("name")).lower()))
    return sorted(results, key=lambda item: as_text(item.get(sort_by.lower())).lower())


def render_list(label: str, values: object) -> None:
    st.write(f"**{label}**")
    items = as_list(values)
    if not items:
        st.caption("Not provided")
        return
    for item in items:
        st.write(f"- {item}")


def render_mapping(label: str, value: object) -> None:
    st.write(f"**{label}**")
    if isinstance(value, Mapping):
        st.json(dict(value))
    else:
        st.write(as_text(value))


def render_big_five(value: object) -> None:
    st.write("**Big Five Personality**")
    if not isinstance(value, Mapping):
        st.caption("Not provided")
        return

    for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
        try:
            score = float(str(value.get(trait, 0)).replace("%", ""))
        except ValueError:
            score = 0.0
        normalized = max(0.0, min(score, 100.0))
        st.progress(normalized / 100, text=f"{trait.replace('_', ' ').title()}: {normalized:.0f}")


def render_persona_card(persona: dict) -> None:
    with st.container(border=True):
        avatar_col, summary_col = st.columns([1, 4])
        with avatar_col:
            st.image(avatar_url(persona), width=112)
        with summary_col:
            st.subheader(as_text(persona.get("name"), "Unknown"))
            st.caption(f"{as_text(persona.get('occupation'))} | {as_text(persona.get('gender'))} | Age {as_text(persona.get('age'))}")
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Income", as_text(persona.get("income")))
            metric_col2.metric("Education", as_text(persona.get("education")))
            metric_col3.metric("Quality", as_text(persona.get("quality_score"), "N/A"))

            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
            score_col1.metric("Diversity", as_text(persona.get("diversity_score"), "N/A"))
            score_col2.metric("Validation", as_text(persona.get("validation_score"), "N/A"))
            score_col3.metric("Completeness", as_text(persona.get("completeness_score"), "N/A"))
            score_col4.metric("Consistency", as_text(persona.get("consistency_score"), "N/A"))

        score_col1, score_col2, score_col3 = st.columns(3)
        score_col1.caption(f"Confidence {as_text(persona.get('persona_confidence_score'), 'N/A')}%")
        score_col2.caption(f"Realism {as_text(persona.get('realism_score'), 'N/A')}%")
        score_col3.caption(f"Consistency {as_text(persona.get('consistency_score'), 'N/A')}%")


        st.write(as_text(persona.get("bio"), "No biography provided."))
        st.caption(f"Location: {as_text(persona.get('city') or persona.get('location'))} | Lifestyle: {as_text(persona.get('lifestyle'))}")

        content_col1, content_col2 = st.columns(2)
        with content_col1:
            render_list("Goals", persona.get("goals"))
            render_mapping("Psychological Profile", persona_value(persona, "psychological_profile", {}))
        with content_col2:
            render_list("Pain Points", persona.get("pain_points"))
            render_mapping("Behavior Pattern", persona_value(persona, "behavior_pattern", {}))

        profile_col1, profile_col2, profile_col3 = st.columns(3)
        with profile_col1:
            st.write("**Technology Usage**")
            st.write(as_text(persona.get("technology_usage")))
        with profile_col2:
            st.write("**Buying Behavior**")
            st.write(as_text(persona_value(persona, "buying_behavior")))
        with profile_col3:
            st.write("**Contact**")
            st.caption(as_text(persona.get("email")))
            st.caption(as_text(persona.get("phone")))

        st.write("**Decision Making**")
        st.write(as_text(persona.get("decision_making")))
        render_big_five(persona_value(persona, "big_five_personality", {}))


def main() -> None:
    st.set_page_config(page_title="Persona Cards", layout="wide")
    init_session_state()
    render_sidebar("Persona Cards")
    render_page_header("Persona Cards", "Review, filter, sort, and export generated personas.")

    personas = require_personas()
    if personas is None:
        return

    view_col, score_col = st.columns([1, 2])
    with view_col:
        view_mode = st.radio("View", ["Gallery", "List"], horizontal=True)
    with score_col:
        st.caption("Quality score combines data completeness, consistency, and behavioral realism.")
    visible_personas = filtered_personas(get_personas())
    st.caption(f"Showing {len(visible_personas)} of {len(personas)} personas")

    export_df = records_to_dataframe(visible_personas)
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "Download filtered JSON",
            data=json.dumps(visible_personas, indent=2).encode("utf-8"),
            file_name="personas.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            "Download filtered CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="personas.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if not visible_personas:
        st.info("No personas match the current filters.")
        return

    if view_mode == "List":
        st.dataframe(records_to_dataframe(visible_personas), use_container_width=True, hide_index=True)
    else:
        for start in range(0, len(visible_personas), 2):
            columns = st.columns(2)
            for column, persona in zip(columns, visible_personas[start:start + 2]):
                with column:
                    render_persona_card(persona)


if __name__ == "__main__":
    main()
