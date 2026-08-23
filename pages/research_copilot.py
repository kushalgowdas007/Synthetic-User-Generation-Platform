from __future__ import annotations

import json
import streamlit as st

from frontend.shared import (
    get_experiment,
    increment_state_version,
    init_session_state,
    render_page_header,
    render_sidebar,
    render_synthetic_disclaimer,
)
from services.research_copilot import build_research_plan


def main() -> None:
    st.set_page_config(page_title="Research Copilot | AI Research Studio", layout="wide")
    init_session_state()
    render_sidebar("Research Copilot")
    render_page_header(
        "AI Research Blueprint Copilot",
        "Turn a product concept or raw brief into an editable, decision-ready research and validation plan.",
        active_stage="Workspace",
    )

    experiment = get_experiment()
    with st.form("copilot_brief"):
        left, right = st.columns(2)
        with left:
            product_name = st.text_input("Product Name", experiment.get("product_name", ""), placeholder="Orbit expense platform")
            industry = st.text_input("Industry", experiment.get("industry", "Technology"))
            audience = st.text_area("Target Audience", experiment.get("target_audience", ""), height=100)
        with right:
            description = st.text_area("Product Description", experiment.get("description", ""), height=100)
            goals = st.text_area("Research Goals & Objectives", experiment.get("research_objective", ""), height=100)
            create = st.form_submit_button("Generate Research Blueprint", use_container_width=True)

    if create:
        if not product_name.strip() or not description.strip() or not audience.strip() or not goals.strip():
            st.error("Please complete product name, description, audience, and research goals.")
        else:
            brief = {
                "product_name": product_name,
                "description": description,
                "industry": industry,
                "audience": audience,
                "goals": goals,
            }
            with st.spinner("Synthesizing research plan and hypotheses..."):
                st.session_state["research_plan"] = build_research_plan(brief)
                st.session_state["experiment"] = {
                    **experiment,
                    "product_name": product_name,
                    "description": description,
                    "industry": industry,
                    "target_audience": audience,
                    "research_objective": goals,
                    "research_goal": goals,
                }
                increment_state_version()
                st.session_state["toast_message"] = "Research plan generated and applied to the workspace."
                st.rerun()

    plan = st.session_state.get("research_plan")
    if not plan:
        st.info("Fill out the brief above to generate an initial research blueprint before configuring personas.")
    else:
        st.subheader("Editable Research Blueprint")
        edited: dict[str, object] = {}
        for key, value in plan.items():
            label = key.replace("_", " ").title()
            if isinstance(value, list):
                edited[key] = [line for line in st.text_area(label, "\n".join(value), height=110).splitlines() if line.strip()]
            else:
                edited[key] = st.text_area(label, str(value), height=90)
        st.session_state["research_plan"] = edited

        st.divider()
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            st.download_button(
                "Download Research Plan JSON",
                json.dumps(edited, indent=2).encode("utf-8"),
                "research_plan.json",
                "application/json",
                use_container_width=True,
            )
        with exp_col2:
            st.page_link("app.py", label="Continue to Persona Workspace →", use_container_width=True)

    st.divider()
    render_synthetic_disclaimer()


if __name__ == "__main__":
    main()
