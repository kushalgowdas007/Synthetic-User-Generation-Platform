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
    render_synthetic_disclaimer,
    require_personas,
)


def avatar_url(persona: Mapping[str, object]) -> str:
    existing = str(persona.get("avatar_url", "")).strip()
    if existing:
        return existing
    return f"https://api.dicebear.com/9.x/initials/svg?seed={quote(as_text(persona.get('name'), 'Persona'))}"


def filtered_personas(personas: list[dict]) -> list[dict]:
    search_col, gender_col, occupation_col, quality_col, sort_col = st.columns([1.5, 1, 1, 1, 1])
    with search_col:
        search = st.text_input("Search", placeholder="Name, occupation, goal, or pain point")
    with gender_col:
        gender_options = ["All"] + sorted({as_text(persona.get("gender")) for persona in personas if persona.get("gender")})
        gender = st.selectbox("Gender", gender_options)
    with occupation_col:
        occupation_options = ["All"] + sorted({as_text(persona.get("occupation")) for persona in personas if persona.get("occupation")})
        occupation = st.selectbox("Occupation", occupation_options)
    with quality_col:
        quality_filter = st.selectbox("Quality Status", ["All", "Valid (>=70)", "Needs Review (<70)"])
    with sort_col:
        sort_by = st.selectbox("Sort", ["Quality Score", "Name", "Age", "Gender", "Occupation", "Income"])

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
        q_score = int(persona.get("quality_score", 80) or 80)
        if quality_filter == "Valid (>=70)" and q_score < 70:
            continue
        if quality_filter == "Needs Review (<70)" and q_score >= 70:
            continue
        results.append(persona)

    if sort_by == "Quality Score":
        return sorted(results, key=lambda item: int(item.get("quality_score", 0) or 0), reverse=True)
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
    q_score = int(persona.get("quality_score", 80) or 80)
    status_label = "Valid" if q_score >= 70 else "Needs Review"
    badge_color = "#10b981" if q_score >= 70 else "#f59e0b"

    with st.container(border=True):
        avatar_col, summary_col = st.columns([1, 4])
        with avatar_col:
            st.image(avatar_url(persona), width=112)
            st.markdown(
                f'<span style="background:{badge_color};color:white;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;">'
                f'{status_label}</span>',
                unsafe_allow_html=True,
            )
        with summary_col:
            st.subheader(as_text(persona.get("name"), "Unknown"))
            st.caption(f"{as_text(persona.get('occupation'))} | {as_text(persona.get('gender'))} | Age {as_text(persona.get('age'))}")
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            metric_col1.metric("Income", as_text(persona.get("income")))
            metric_col2.metric("Education", as_text(persona.get("education")))
            metric_col3.metric("Quality Score", f"{q_score}/100")

        st.caption(
            f"Completeness: {persona.get('completeness_score', 'N/A')} | "
            f"Coherence: {persona.get('coherence_score', 'N/A')} | "
            f"Diversity: {persona.get('diversity_score', 'N/A')} | "
            f"Consistency: {persona.get('behavioral_consistency_score', persona.get('consistency_score', 'N/A'))} | "
            f"Usefulness: {persona.get('research_usefulness_score', 'N/A')}"
        )

        warnings = persona.get("quality_warnings", [])
        if warnings:
            with st.expander("⚠ Quality Diagnostics & Warnings", expanded=False):
                for w in warnings:
                    st.warning(f"• {w}")

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

        render_big_five(persona_value(persona, "big_five_personality", {}))


def render_comparison_matrix(personas: list[dict]) -> None:
<<<<<<< HEAD
    """Renders a responsive side-by-side comparison matrix for 2-4 selected personas."""
    st.subheader("⚖ Persona Comparison Matrix")
    persona_options = {p.get("id", str(idx)): f"{p.get('name', 'Persona')} ({p.get('occupation', 'Role')})" for idx, p in enumerate(personas)}
    default_selected = list(persona_options.keys())[:min(3, len(personas))]

    selected_ids = st.multiselect(
        "Select 2 to 4 personas to compare side-by-side:",
        options=list(persona_options.keys()),
        default=default_selected,
        format_func=persona_options.get,
        max_selections=4,
    )

    if len(selected_ids) < 2:
        st.info("Select at least 2 personas above to view the side-by-side comparison matrix.")
        return

    selected_personas = [p for p in personas if p.get("id", "") in selected_ids or str(personas.index(p)) in selected_ids]
    cols = st.columns(len(selected_personas))

    comparison_fields = [
        ("Occupation", "occupation"),
        ("Age / Gender", lambda p: f"{p.get('age', 'N/A')} / {p.get('gender', 'N/A')}"),
        ("Income", "income"),
        ("Technology Usage", "technology_usage"),
        ("Buying Behavior", lambda p: persona_value(p, "buying_behavior", "N/A")),
        ("Top Goal", lambda p: (as_list(p.get("goals")) or ["N/A"])[0]),
        ("Top Pain Point", lambda p: (as_list(p.get("pain_points")) or ["N/A"])[0]),
        ("Quality Score", lambda p: f"{p.get('quality_score', 'N/A')}/100"),
        ("Decision Style", lambda p: (persona_value(p, "psychological_profile", {}) or {}).get("decision_style", "Research-led")),
    ]

    for col, persona in zip(cols, selected_personas):
        with col:
            with st.container(border=True):
                st.markdown(f"### {persona.get('name', 'Persona')}")
                st.caption(f"{persona.get('city', 'India')} | {persona.get('lifestyle', 'Balanced')}")
                st.divider()
                for label, field_getter in comparison_fields:
                    val = field_getter(persona) if callable(field_getter) else persona.get(field_getter, "N/A")
                    st.markdown(f"**{label}**")
                    st.write(str(val))
                    st.markdown("<hr style='margin:4px 0;opacity:0.2'/>", unsafe_allow_html=True)
=======
    """Render Phase 14 side-by-side persona comparison matrix for 2-4 selected personas."""
    with st.expander("⚖ Persona Comparison Matrix (Select 2–4 Personas)", expanded=False):
        if len(personas) < 2:
            st.info("At least 2 personas are required for comparison.")
            return

        names = [str(p.get("name", f"Persona {idx+1}")) for idx, p in enumerate(personas)]
        selected_names = st.multiselect("Select Personas to Compare", names, default=names[:min(4, len(names))])

        if len(selected_names) < 2:
            st.warning("Please select at least 2 personas to view comparison.")
            return

        selected_personas = [p for p in personas if str(p.get("name")) in selected_names]

        # Side-by-side layout
        cols = st.columns(len(selected_personas))
        for idx, (col, persona) in enumerate(zip(cols, selected_personas)):
            with col:
                st.subheader(str(persona.get("name")))
                st.caption(f"{persona.get('occupation')} | Age {persona.get('age')}")
                st.metric("Quality Score", f"{persona.get('quality_score', 80)}/100")
                st.metric("Income", str(persona.get("income", "N/A")))
                st.metric("Tech Usage", str(persona.get("technology_usage", "Medium")))
                
                st.write("**Top Goals:**")
                for g in as_list(persona.get("goals"))[:3]:
                    st.write(f"- {g}")
                    
                st.write("**Top Pain Points:**")
                for p in as_list(persona.get("pain_points"))[:3]:
                    st.write(f"- {p}")
                    
                st.write("**Buying Behavior:**")
                st.caption(str(persona_value(persona, "buying_behavior")))
>>>>>>> f68520b (Save local changes)


def main() -> None:
    st.set_page_config(page_title="Persona Cards", layout="wide")
    init_session_state()
    render_sidebar("Persona Cards")
<<<<<<< HEAD
    render_page_header(
        "Persona Cards & Quality Inspection",
        "Review, filter, inspect quality scores, compare cohorts, and export generated personas.",
        active_stage="Persona Cards",
    )
=======
    render_page_header("Persona Cards", "Review, filter, sort, compare, and export generated personas.")
>>>>>>> f68520b (Save local changes)

    personas = require_personas()
    if personas is None:
        return

<<<<<<< HEAD
    tabs = st.tabs(["📇 Persona Gallery / List", "⚖ Side-by-Side Comparison Matrix"])
=======
    render_comparison_matrix(personas)

    view_col, score_col = st.columns([1, 2])
    with view_col:
        view_mode = st.radio("View", ["Gallery", "List"], horizontal=True)
    with score_col:
        st.caption("Quality score combines data completeness, consistency, and behavioral realism.")
    visible_personas = filtered_personas(get_personas())
    st.caption(f"Showing {len(visible_personas)} of {len(personas)} personas")
>>>>>>> f68520b (Save local changes)

    with tabs[0]:
        view_col, score_col = st.columns([1, 2])
        with view_col:
            view_mode = st.radio("View Mode", ["Gallery", "List"], horizontal=True)
        with score_col:
            st.caption("◈ Persona Quality Score (0–100) measures data completeness, demographic coherence, and behavioral realism.")

        visible_personas = filtered_personas(get_personas())
        st.caption(f"Showing {len(visible_personas)} of {len(personas)} personas")

<<<<<<< HEAD
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
        elif view_mode == "List":
            st.dataframe(records_to_dataframe(visible_personas), use_container_width=True, hide_index=True)
        else:
            for start in range(0, len(visible_personas), 2):
                columns = st.columns(2)
                for column, persona in zip(columns, visible_personas[start : start + 2]):
                    with column:
                        render_persona_card(persona)

    with tabs[1]:
        render_comparison_matrix(get_personas())

    st.divider()
    render_synthetic_disclaimer()
=======
    if view_mode == "List":
        st.dataframe(records_to_dataframe(visible_personas), use_container_width=True, hide_index=True)
    else:
        for start in range(0, len(visible_personas), 2):
            columns = st.columns(2)
            for column, persona in zip(columns, visible_personas[start:start + 2]):
                with column:
                    # Check for low quality flag
                    q_score = int(persona.get("quality_score", 80) or 80)
                    if q_score < 70 or persona.get("needs_review"):
                        st.warning("⚠ Needs Review — Quality Score < 70")
                    render_persona_card(persona)
>>>>>>> f68520b (Save local changes)


if __name__ == "__main__":
    main()
