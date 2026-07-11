from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.shared import (
    get_experiment,
    get_insights,
    get_interview_results,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)
from services.insight_agent import extract_research_insights


def main() -> None:
    st.set_page_config(page_title="Insights", layout="wide")
    init_session_state()
    render_sidebar("Insights")
    render_page_header("Insight Extraction", "Extract themes, sentiment, behavior patterns, quotes, recommendations, and product-fit signals.")

    personas = require_personas()
    if personas is None:
        return

    survey_results = get_survey_results()
    interview_rows = get_interview_results()
    if not survey_results and not interview_rows:
        st.warning("Run the Survey or conduct at least one Interview before extracting insights.")
        st.page_link("pages/survey.py", label="Open Survey")
        st.page_link("pages/interview.py", label="Open Interview")
        return

    if st.button("Extract Insights", use_container_width=True):
        with st.spinner("Extracting research insights..."):
            st.session_state["insights"] = extract_research_insights(
                experiment=get_experiment(),
                personas=personas,
                survey_results=survey_results,
                interview_rows=interview_rows,
            )
        st.success("Insights extracted successfully.")

    insights = get_insights()
    if not insights:
        st.info("Click Extract Insights to build the research summary.")
        return

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Sentiment", str(insights.get("sentiment", "N/A")).title())
    metric_col2.metric("Would Use Score", f"{float(insights.get('would_use_product_score', 0) or 0):.1f}")
    metric_col3.metric("Survey Responses", insights.get("response_count", 0))
    metric_col4.metric("Interview Messages", insights.get("interview_message_count", 0))

    theme_df = pd.DataFrame(insights.get("themes", []))
    if not theme_df.empty:
        st.plotly_chart(px.bar(theme_df, x="theme", y="count", title="Theme Frequency"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Recommendations")
        for recommendation in insights.get("recommendations", []):
            st.write(f"- {recommendation}")
    with col2:
        st.subheader("Top Quotes")
        for quote in insights.get("top_quotes", []):
            st.write(f"> {quote}")

    with st.expander("Persona Segmentation", expanded=False):
        st.json(insights.get("persona_segmentation", {}))

    st.download_button(
        "Download insights JSON",
        data=json.dumps(insights, indent=2).encode("utf-8"),
        file_name="research_insights.json",
        mime="application/json",
        use_container_width=True,
    )
    st.page_link("pages/dashboard.py", label="Open Dashboard")


if __name__ == "__main__":
    main()
