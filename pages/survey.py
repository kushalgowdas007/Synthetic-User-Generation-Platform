from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from backend.services.survey_service import DEFAULT_SURVEY_QUESTIONS, execute_survey
from frontend.shared import (
    get_experiment,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)


def main() -> None:
    st.set_page_config(page_title="Survey", layout="wide")
    init_session_state()
    render_sidebar("Survey")
    render_page_header("Survey", "Generate simulated survey responses from the personas already stored in session state.")

    personas = require_personas()
    if personas is None:
        return

    experiment = get_experiment()
    default_product = str(experiment.get("product_name") or "").strip()
    default_goal = str(experiment.get("research_objective") or experiment.get("research_goal") or "").strip()

    st.success(f"{len(personas)} personas loaded from st.session_state['personas'].")

    with st.expander("Survey questions", expanded=False):
        for question in DEFAULT_SURVEY_QUESTIONS:
            st.write(f"**{question['id']}** - {question['question']}")

    with st.form("survey_form"):
        product_name = st.text_input("Product Name", value=default_product)
        research_goal = st.text_area("Research Objective", value=default_goal, height=120)
        submitted = st.form_submit_button("Run Survey", use_container_width=True)

    if submitted:
        if not product_name.strip() or not research_goal.strip():
            st.error("Please provide both Product Name and Research Objective.")
            return

        try:
            with st.spinner("Generating survey responses..."):
                survey_results = execute_survey(
                    personas,
                    product_name=product_name.strip(),
                    research_goal=research_goal.strip(),
            )
            st.session_state["survey_results"] = survey_results
            st.session_state["insights"] = None
            st.success("Survey completed successfully.")
        except Exception as exc:
            st.error(f"Unable to run the survey. Detail: {exc}")
            return

    survey_results = get_survey_results()
    if not survey_results:
        st.info("Run the survey to generate responses and unlock the dashboard.")
        return

    responses = survey_results.get("responses", [])
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Personas", len(personas))
    metric_col2.metric("Responses", len(responses))
    metric_col3.metric("Product Fit", f"{float(survey_results.get('product_fit_score', 0) or 0):.1f} / 100")

    responses_df = pd.DataFrame(responses)
    if not responses_df.empty:
        st.subheader("Survey Responses")
        st.dataframe(responses_df, use_container_width=True, hide_index=True)

        st.download_button(
            "Download survey results JSON",
            data=json.dumps(survey_results, indent=2).encode("utf-8"),
            file_name="survey_results.json",
            mime="application/json",
            use_container_width=True,
        )
        st.page_link("pages/dashboard.py", label="Open Dashboard")
        st.page_link("pages/interview.py", label="Open Interview")
        st.page_link("pages/insights.py", label="Open Insights")


if __name__ == "__main__":
    main()
