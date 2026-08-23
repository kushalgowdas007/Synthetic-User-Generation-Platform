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
    increment_state_version,
    init_session_state,
    render_page_header,
    render_sidebar,
    render_synthetic_disclaimer,
    require_personas,
)
from services.insight_agent import extract_research_insights


def render_structured_insight_card(item: dict) -> None:
    title = item.get("title", "Insight")
    itype = item.get("type", "General")
    importance = item.get("severity_or_importance", item.get("severity", 70))
    confidence = item.get("confidence", 80)
    aff_count = item.get("affected_personas_count", len(item.get("affected_personas", [])))
    aff_personas = item.get("affected_personas", [])
    evidence_list = item.get("evidence", [])
    recommendation = item.get("recommendation", "")

    type_colors = {
        "Theme": "#6366f1",
        "Pain Point": "#ef4444",
        "Opportunity": "#10b981",
        "Contradiction": "#f59e0b",
        "Risk": "#dc2626",
        "Positive Signal": "#059669",
        "Behavioral Pattern": "#8b5cf6",
        "Segment Difference": "#0284c7",
    }
    badge_bg = type_colors.get(itype, "#64748b")

    with st.container(border=True):
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            st.markdown(
                f'<span style="background:{badge_bg};color:white;padding:3px 9px;border-radius:6px;font-size:11px;font-weight:bold;margin-right:8px;">{itype}</span>'
                f'<b style="font-size:1.05rem;">{title}</b>',
                unsafe_allow_html=True,
            )
        with head_col2:
            st.caption(f"Importance: **{importance}/100** | Conf: **{confidence}%**")

        st.caption(f"Affected Personas ({aff_count}): {', '.join(aff_personas[:4]) if aff_personas else 'Cohort Wide'}")

        if evidence_list:
            st.markdown("**Evidence Traceability (Why?):**")
            for ev in evidence_list:
                if isinstance(ev, dict):
                    src = ev.get("source_type", "Source")
                    det = ev.get("source_detail", "")
                    quote = ev.get("metric_or_quote", "")
                    st.markdown(f"- 🔍 _[{src.upper()}]_ **{det}**: {quote}")
                else:
                    st.markdown(f"- 🔍 {ev}")
        else:
            st.markdown("- 🔍 _Insufficient quantitative evidence recorded._")

        if recommendation:
            st.info(f"💡 **Recommended Action:** {recommendation}")


def main() -> None:
    st.set_page_config(page_title="Insights", layout="wide")
    init_session_state()
    render_sidebar("Insights")
    render_page_header(
        "Insight Clustering & Evidence Traceability",
        "Organize research findings into 8 structured categories with verifiable evidence from surveys and interviews.",
        active_stage="Insights",
    )

    personas = require_personas()
    if personas is None:
        return

    survey_results = get_survey_results()
    interview_rows = get_interview_results()
    focus_rows = st.session_state.get("focus_group_results", [])
    
    has_research_data = bool(survey_results or interview_rows or focus_rows)
    if not has_research_data:
        st.warning("Run the Survey, conduct an Interview, or moderate a Focus Group before extracting insights.")
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        with nav_col1:
            st.page_link("pages/survey.py", label="Open Survey")
        with nav_col2:
            st.page_link("pages/interview.py", label="Open Interview")
        with nav_col3:
            st.page_link("pages/focus_group.py", label="Open Focus Group")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        extract_clicked = st.button("🚀 Extract & Cluster Research Insights", use_container_width=True)
    with col2:
        bypass_cache = st.checkbox("Bypass cache", value=False, help="Force re-extraction of insights")

    if extract_clicked:
        with st.spinner("Clustering findings into 8 insight categories and tracing evidence..."):
            st.session_state["insights"] = extract_research_insights(
                experiment=get_experiment(),
                personas=personas,
                survey_results=survey_results,
                interview_rows=interview_rows,
                focus_rows=focus_rows,
                bypass_cache=bypass_cache,
            )
            st.session_state["consultant_report"] = None
            st.session_state["product_actions"] = []
            increment_state_version()
        st.success("Insights extracted and structured successfully.")

    insights = get_insights()
    if not insights:
        st.info("Click 'Extract & Cluster Research Insights' to organize your research data.")
        return

    # Top KPI Metrics
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Overall Sentiment", str(insights.get("sentiment", "N/A")).title())
    metric_col2.metric("Product Fit Score", f"{float(insights.get('product_fit_score', 0) or 0):.1f}/100")
    metric_col3.metric("Survey Data Points", insights.get("response_count", 0))
    metric_col4.metric("Qualitative Turns", insights.get("interview_message_count", 0))

    st.info(f"📋 **Executive Research Summary:** {insights.get('executive_summary', '')}")

    # 8 Structured Insight Category Tabs
    st.subheader("Clustered Findings & Evidence")
    clusters = insights.get("structured_clusters", {})

    insight_tabs = st.tabs([
        "1. Themes",
        "2. Pain Points",
        "3. Opportunities",
        "4. Contradictions",
        "5. Risks",
        "6. Positive Signals",
        "7. Behavioral Patterns",
        "8. Segment Differences",
    ])

    tab_mappings = [
        ("themes", insight_tabs[0]),
        ("pain_points", insight_tabs[1]),
        ("opportunities", insight_tabs[2]),
        ("contradictions", insight_tabs[3]),
        ("risks", insight_tabs[4]),
        ("positive_signals", insight_tabs[5]),
        ("behavioral_patterns", insight_tabs[6]),
        ("segment_differences", insight_tabs[7]),
    ]

    for key, tab in tab_mappings:
        with tab:
            items = clusters.get(key, [])
            if not items:
                st.info(f"No specific records identified for this category.")
            else:
                for item in items:
                    render_structured_insight_card(item)

    st.divider()

    # Visualizations
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        theme_df = pd.DataFrame(insights.get("themes", []))
        if not theme_df.empty:
            st.plotly_chart(px.bar(theme_df, x="theme", y="count", title="Theme Mention Frequency", color="count"), use_container_width=True)
    with chart_col2:
        sentiment_distribution = insights.get("sentiment_distribution", {})
        if sentiment_distribution:
            sentiment_df = pd.DataFrame(
                [
                    {"Sentiment": k.title(), "Count": v.get("count", 0)}
                    for k, v in sentiment_distribution.items()
                    if isinstance(v, dict)
                ]
            )
            if not sentiment_df.empty:
                st.plotly_chart(px.pie(sentiment_df, names="Sentiment", values="Count", title="Cohort Sentiment Distribution"), use_container_width=True)

    # Top Quotes & AI Recommendations
    q_col, r_col = st.columns(2)
    with q_col:
        st.subheader("Verbatim Persona Quotes")
        for q in insights.get("top_quotes", []):
            if isinstance(q, dict):
                st.markdown(f"> \"{q.get('quote', '')}\"")
                st.caption(f"— **{q.get('persona_name', 'Persona')}** ({q.get('source', 'session')})")
            else:
                st.markdown(f"> \"{q}\"")

    with r_col:
        st.subheader("AI Synthesized Recommendations")
        for rec in insights.get("final_ai_recommendations", []):
            if isinstance(rec, dict):
                st.markdown(f"• **{rec.get('recommendation', '')}** _(Confidence: {rec.get('confidence_score', 80)}%)_")
            else:
                st.markdown(f"• {rec}")

    st.divider()
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button(
            "Download Structured Insights JSON",
            data=json.dumps(insights, indent=2).encode("utf-8"),
            file_name="research_insights.json",
            mime="application/json",
            use_container_width=True,
        )
    with download_col2:
        st.page_link("pages/consultant.py", label="Proceed to Product Consultant & Decision Action Center →", use_container_width=True)

    st.divider()
    render_synthetic_disclaimer()


if __name__ == "__main__":
    main()
