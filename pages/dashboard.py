from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Mapping

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.services.survey_service import build_dashboard_payload
from frontend.shared import (
    age_number,
    as_list,
    get_experiment,
    get_insights,
    get_interview_results,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)
from services.report_service import export_full_research_report_pdf


def persona_dataframe(personas: list[Mapping[str, Any]]) -> pd.DataFrame:
    rows = []
    for persona in personas:
        rows.append(
            {
                "name": persona.get("name", "Unknown"),
                "age": age_number(persona.get("age")),
                "gender": persona.get("gender", "Not provided"),
                "occupation": persona.get("occupation", "Not provided"),
                "technology_usage": persona.get("technology_usage", "Not provided"),
                "buying_behavior": persona.get("buying_behavior") or persona.get("buying_behaviour") or "Not provided",
                "quality_score": persona.get("quality_score", 0),
            }
        )
    return pd.DataFrame(rows)


def build_report_download(
    *,
    experiment: Mapping[str, Any],
    personas: list[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: list[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
    analytics: Mapping[str, Any] | None,
) -> bytes:
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": dict(experiment),
        "personas": [dict(persona) for persona in personas],
        "survey_results": dict(survey_results or {}),
        "interview_results": [dict(row) for row in interview_rows],
        "insights": dict(insights or {}),
        "analytics": dict(analytics or {}),
    }
    return json.dumps(report, indent=2, default=str).encode("utf-8")


def render_counter_chart(counter: Counter[str], names: tuple[str, str], title: str) -> None:
    frame = pd.DataFrame(counter.most_common(8), columns=list(names))
    if frame.empty:
        st.info(f"No {names[0].lower()} data is available yet.")
        return
    st.plotly_chart(px.bar(frame, x=names[1], y=names[0], orientation="h", title=title), use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Dashboard", layout="wide")
    init_session_state()
    render_sidebar("Dashboard")
    render_page_header("Dashboard", "Analytics from the shared personas, survey results, and experiment configuration.")

    personas = require_personas()
    if personas is None:
        return

    experiment = get_experiment()
    survey_results = get_survey_results()
    interview_rows = get_interview_results()
    insights = get_insights()
    consultant = st.session_state.get("consultant_report") or {}
    persona_df = persona_dataframe(personas)
    age_values = [value for value in persona_df["age"].dropna().tolist()]
    average_age = round(sum(age_values) / len(age_values), 1) if age_values else 0
    product_fit = float(survey_results.get("product_fit_score", 0) or 0) if survey_results else 0

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Total Personas", len(personas))
    metric_col2.metric("Average Age", average_age)
    metric_col3.metric("Product Fit", f"{product_fit:.1f} / 100" if survey_results else "Pending")
    metric_col4.metric("Survey Responses", len(survey_results.get("responses", [])) if survey_results else 0)

    extra_col1, extra_col2 = st.columns(2)
    extra_col1.metric("Interview Messages", len(interview_rows))
    extra_col2.metric("Recommendation Score", f"{float((insights or {}).get('would_use_product_score', 0) or 0):.1f} / 100" if insights else "Pending")
    if consultant:
        readiness_col1, readiness_col2 = st.columns(2)
        readiness_col1.metric("Launch Readiness", f"{consultant.get('launch_readiness', 0)}%")
        readiness_col2.metric("Risk Score", f"{consultant.get('risk_score', 0)}/100")

    if experiment:
        with st.expander("Experiment", expanded=False):
            st.json(experiment)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        gender_counts = persona_df["gender"].fillna("Not provided").value_counts().reset_index()
        gender_counts.columns = ["Gender", "Count"]
        st.plotly_chart(px.pie(gender_counts, names="Gender", values="Count", title="Gender Distribution"), use_container_width=True)
    with chart_col2:
        occupation_counts = persona_df["occupation"].fillna("Not provided").value_counts().reset_index()
        occupation_counts.columns = ["Occupation", "Count"]
        st.plotly_chart(px.bar(occupation_counts, x="Occupation", y="Count", title="Occupation Distribution"), use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        st.plotly_chart(px.histogram(persona_df, x="age", nbins=10, title="Age Distribution"), use_container_width=True)
    with chart_col4:
        st.plotly_chart(px.bar(persona_df, x="name", y="quality_score", title="Persona Quality Score"), use_container_width=True)

    pain_counter: Counter[str] = Counter()
    goal_counter: Counter[str] = Counter()
    for persona in personas:
        pain_counter.update(as_list(persona.get("pain_points")))
        goal_counter.update(as_list(persona.get("goals")))

    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        render_counter_chart(pain_counter, ("Pain Point", "Count"), "Top Pain Points")
    with detail_col2:
        render_counter_chart(goal_counter, ("Goal", "Count"), "Top Goals")

    analytics: Dict[str, Any] | None = None
    if survey_results and survey_results.get("responses"):
        responses_df = pd.DataFrame(survey_results["responses"])
        analytics = build_dashboard_payload(
            survey_results["responses"],
            personas=personas,
            product_name=survey_results.get("product_name", experiment.get("product_name", "")),
            research_goal=survey_results.get("research_goal", experiment.get("research_objective", "")),
        )

        st.subheader("Survey Analytics")
        response_col1, response_col2 = st.columns(2)
        with response_col1:
            fit_by_persona = responses_df.groupby("persona_name")["score"].mean().reset_index()
            st.plotly_chart(px.bar(fit_by_persona, x="persona_name", y="score", title="Product Fit by Persona"), use_container_width=True)
        with response_col2:
            fit_by_question = responses_df.groupby("question_id")["score"].mean().reset_index()
            st.plotly_chart(px.line(fit_by_question, x="question_id", y="score", markers=True, title="Average Fit by Question"), use_container_width=True)

        st.dataframe(responses_df, use_container_width=True, hide_index=True)

        with st.expander("Research report", expanded=True):
            st.json(analytics.get("research_report", {}))
    else:
        st.info("Run the survey to populate product fit analytics and report exports.")
        st.page_link("pages/survey.py", label="Open Survey")

    if insights:
        st.subheader("Insight Analytics")
        theme_df = pd.DataFrame(insights.get("themes", []))
        insight_col1, insight_col2, insight_col3 = st.columns(3)
        with insight_col1:
            if not theme_df.empty:
                st.plotly_chart(px.bar(theme_df, x="theme", y="count", title="Theme Frequency"), use_container_width=True)
            else:
                st.info("No theme frequency data available.")
        with insight_col2:
            st.metric("Sentiment", str(insights.get("sentiment", "N/A")).title())
            st.metric("Recommendation Score", f"{float(insights.get('would_use_product_score', 0) or 0):.1f} / 100")
        with insight_col3:
            sentiment_frame = pd.DataFrame([{"Sentiment": str(insights.get("sentiment", "neutral")).title(), "Responses": insights.get("response_count", 0)}])
            st.plotly_chart(px.bar(sentiment_frame, x="Sentiment", y="Responses", title="Sentiment Signal"), use_container_width=True)
        with st.expander("Recommendations", expanded=True):
            for item in insights.get("recommendations", []):
                st.write(f"- {item}")
    else:
        st.info("Extract insights to complete the research dashboard.")
        st.page_link("pages/insights.py", label="Open Insights")

    completion_frame = pd.DataFrame([
        {"Stage": "Generated personas", "Complete": len(personas)},
        {"Stage": "Survey responses", "Complete": len(survey_results.get("responses", [])) if survey_results else 0},
        {"Stage": "Interview messages", "Complete": len(interview_rows)},
        {"Stage": "Focus group turns", "Complete": len(st.session_state.get("focus_group_results", []))},
    ])
    st.plotly_chart(px.bar(completion_frame, x="Stage", y="Complete", title="Workflow Completion"), use_container_width=True)

    st.subheader("Download Report")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        st.download_button(
            "Download JSON report",
            data=build_report_download(
                experiment=experiment,
                personas=personas,
                survey_results=survey_results,
                interview_rows=interview_rows,
                insights=insights,
                focus_group_results=st.session_state.get("focus_group_results", []),
                consultant_report=consultant,
                analytics=analytics,
            ),
            file_name="synthetic_user_report.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_col2:
        if analytics or insights:
            pdf_bytes = export_full_research_report_pdf(
                experiment=experiment,
                personas=personas,
                survey_results=survey_results,
                interview_rows=interview_rows,
                insights=insights,
            )
            if pdf_bytes:
                st.download_button(
                    "Download PDF report",
                    data=pdf_bytes,
                    file_name="synthetic_user_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.caption("PDF export requires reportlab from requirements.txt.")


if __name__ == "__main__":
    main()
