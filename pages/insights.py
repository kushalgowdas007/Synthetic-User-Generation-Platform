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
    focus_rows = [
        {"role": "persona", "message": turn.get("message", ""), "persona_name": turn.get("speaker", "")}
        for turn in st.session_state.get("focus_group_results", []) if turn.get("role") == "participant"
    ]
    combined_rows = [*interview_rows, *focus_rows]
    if not survey_results and not combined_rows:
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
                interview_rows=combined_rows,
            )
        st.success("Insights extracted successfully.")

    insights = get_insights()
    if not insights:
        st.info("Click Extract Insights to build the research summary.")
        return

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Sentiment", str(insights.get("sentiment", "N/A")).title())
    metric_col2.metric("Product Fit", f"{float(insights.get('product_fit_score', 0) or 0):.1f}")
    metric_col3.metric("Survey Responses", insights.get("response_count", 0))

    metric_col4.metric("Interview Messages", insights.get("interview_message_count", 0))
    score_col1, score_col2 = st.columns(2)
    score_col1.metric(
        "Recommendation Score",
        f"{float(insights.get('recommendation_score', insights.get('would_use_product_score', 0)) or 0):.1f}",
        help=f"Confidence {insights.get('recommendation_confidence_score', 0)}",
    )
    score_col2.metric(
        "Product Fit Confidence",
        f"{float(insights.get('product_fit_confidence_score', 0) or 0):.0f}",
    )

    metric_col4.metric("Conversation Signals", insights.get("interview_message_count", 0))
    st.caption(f"Analysis confidence: {float(insights.get('confidence_score', 0) or 0):.0f}%")
    st.info(str(insights.get("executive_summary", "")))


    theme_df = pd.DataFrame(insights.get("themes", []))
    if not theme_df.empty:
        st.plotly_chart(px.bar(theme_df, x="theme", y="count", title="Theme Frequency"), use_container_width=True)
        st.dataframe(theme_df, use_container_width=True, hide_index=True)

    sentiment_distribution = insights.get("sentiment_distribution", {})
    if sentiment_distribution:
        sentiment_df = pd.DataFrame(
            [
                {"Sentiment": key.title(), "Count": value.get("count", 0), "Confidence": value.get("confidence_score", 0)}
                for key, value in sentiment_distribution.items()
                if isinstance(value, dict)
            ]
        )
        if not sentiment_df.empty:
            st.plotly_chart(px.pie(sentiment_df, names="Sentiment", values="Count", title="Sentiment Distribution"), use_container_width=True)
            st.dataframe(sentiment_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Final AI Recommendations")
        for item in insights.get("final_ai_recommendations", []):
            if isinstance(item, dict):
                st.write(f"- {item.get('recommendation', '')} _(confidence {item.get('confidence_score', 0)})_")
            else:
                st.write(f"- {item}")
    with col2:
        st.subheader("Top Quotes")
        for quote in insights.get("top_quotes", []):
            if isinstance(quote, dict):
                st.write(f"> {quote.get('quote', '')}")
                st.caption(f"{quote.get('persona_name', 'Persona')} | {quote.get('source', 'research')} | Confidence {quote.get('confidence_score', 0)}")
            else:
                st.write(f"> {quote}")

    detail_tabs = st.tabs(["Keywords", "Pain Points", "Feature Requests", "Behavior", "Barriers", "Early Adopters"])
    tab_payloads = [
        insights.get("keywords", []),
        insights.get("pain_points", []),
        insights.get("feature_requests", []),
        insights.get("behavior_patterns", []),
        insights.get("product_adoption_barriers", []),
        insights.get("early_adopter_detection", []),
    ]
    for tab, payload in zip(detail_tabs, tab_payloads):
        with tab:
            frame = pd.DataFrame(payload)
            if frame.empty:
                st.info("No records available for this insight category.")
            else:
                st.dataframe(frame, use_container_width=True, hide_index=True)

    with st.expander("Persona Segmentation", expanded=False):
        st.json(insights.get("persona_segmentation", {}))
    with st.expander("Topic clusters, keywords, and risks", expanded=False):
        st.write("**Topic clusters**")
        st.json(insights.get("topic_clusters", []))
        st.write("**Keyword frequency**")
        st.json(insights.get("keyword_frequency", []))
        st.write("**Risk analysis**")
        for risk in insights.get("risk_analysis", []):
            st.write(f"- {risk}")

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
