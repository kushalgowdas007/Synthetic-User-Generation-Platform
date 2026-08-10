from __future__ import annotations

import json
import streamlit as st

from frontend.shared import get_experiment, init_session_state, render_page_header, render_sidebar
from services.research_copilot import build_research_plan


def main() -> None:
    st.set_page_config(page_title="Research Copilot | AI Research Studio", layout="wide")
    init_session_state(); render_sidebar("Research Copilot")
    render_page_header("Research Copilot", "Turn a product brief into an editable, decision-ready research plan.")
    experiment = get_experiment()
    with st.form("copilot_brief"):
        left, right = st.columns(2)
        with left:
            product_name = st.text_input("Product name", experiment.get("product_name", ""), placeholder="Orbit expense platform")
            industry = st.text_input("Industry", experiment.get("industry", "Technology"))
            audience = st.text_area("Audience", experiment.get("target_audience", ""), height=100)
        with right:
            description = st.text_area("Product description", experiment.get("description", ""), height=100)
            goals = st.text_area("Research goals", experiment.get("research_objective", ""), height=100)
            create = st.form_submit_button("Generate research plan", use_container_width=True)
    if create:
        if not product_name.strip() or not description.strip() or not audience.strip() or not goals.strip():
            st.error("Complete product name, description, audience, and research goals.")
        else:
            brief = {"product_name": product_name, "description": description, "industry": industry, "audience": audience, "goals": goals}
            st.session_state["research_plan"] = build_research_plan(brief)
            st.session_state["experiment"] = {**experiment, "product_name": product_name, "description": description, "industry": industry, "target_audience": audience, "research_objective": goals, "research_goal": goals}
            st.session_state["toast_message"] = "Research plan generated and applied to the workspace."
            st.rerun()
    plan = st.session_state.get("research_plan")
    if not plan:
        st.info("Start with a brief. The plan remains editable before you generate personas."); return
    st.subheader("Editable research blueprint")
    edited: dict[str, object] = {}
    for key, value in plan.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list): edited[key] = [line for line in st.text_area(label, "\n".join(value), height=110).splitlines() if line.strip()]
        else: edited[key] = st.text_area(label, str(value), height=90)
    st.session_state["research_plan"] = edited
    st.download_button("Download research plan JSON", json.dumps(edited, indent=2).encode(), "research_plan.json", "application/json")
    st.page_link("app.py", label="Continue to Workspace →")


if __name__ == "__main__": main()
