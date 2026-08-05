from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    persona_value,
    render_page_header,
    render_sidebar,
    require_personas,
)
from services.report_service import export_full_research_report_pdf


def _score(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace("%", ""))
    except ValueError:
        return 0.0


def persona_dataframe(personas: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    rows = []
    for persona in personas:
        behavior = persona_value(persona, "behavior_pattern", {})
        if isinstance(behavior, Mapping):
            behavior_summary = ", ".join(str(item) for item in behavior.values() if str(item).strip())
        else:
            behavior_summary = ", ".join(as_list(behavior))
        rows.append(
            {
                "name": persona.get("name", "Unknown"),
                "age": age_number(persona.get("age")),
                "gender": persona.get("gender", "Not provided"),
                "occupation": persona.get("occupation", "Not provided"),
                "education": persona.get("education", "Not provided"),
                "income": persona.get("income", "Not provided"),
                "technology_usage": persona.get("technology_usage", "Not provided"),
                "buying_behavior": persona.get("buying_behavior") or persona.get("buying_behaviour") or "Not provided",
                "behavior": behavior_summary or "Not provided",
                "quality_score": _score(persona.get("quality_score")),
                "diversity_score": _score(persona.get("diversity_score")),
                "validation_score": _score(persona.get("validation_score")),
                "completeness_score": _score(persona.get("completeness_score")),
                "consistency_score": _score(persona.get("consistency_score")),
            }
        )
    return pd.DataFrame(rows)


def build_report_download(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
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


def _filter_personas(personas: Sequence[Mapping[str, Any]]) -> list[dict]:
    frame = persona_dataframe(personas)
    if frame.empty:
        return [dict(persona) for persona in personas]

    st.subheader("Interactive Filters")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1.5, 1, 1, 1])
    with filter_col1:
        search = st.text_input("Search", placeholder="Name, occupation, behavior, or segment")
    with filter_col2:
        occupation = st.selectbox("Occupation", ["All"] + sorted(frame["occupation"].dropna().astype(str).unique().tolist()))
    with filter_col3:
        education = st.selectbox("Education", ["All"] + sorted(frame["education"].dropna().astype(str).unique().tolist()))
    with filter_col4:
        technology = st.selectbox("Technology", ["All"] + sorted(frame["technology_usage"].dropna().astype(str).unique().tolist()))

    filtered: list[dict] = []
    search_text = search.strip().lower()
    for persona in personas:
        row_text = " ".join(
            [
                str(persona.get("name", "")),
                str(persona.get("occupation", "")),
                str(persona.get("education", "")),
                str(persona.get("technology_usage", "")),
                str(persona.get("bio", "")),
                str(persona.get("behavior_pattern", "")),
                str(persona.get("pain_points", "")),
            ]
        ).lower()
        if search_text and search_text not in row_text:
            continue
        if occupation != "All" and str(persona.get("occupation", "Not provided")) != occupation:
            continue
        if education != "All" and str(persona.get("education", "Not provided")) != education:
            continue
        if technology != "All" and str(persona.get("technology_usage", "Not provided")) != technology:
            continue
        filtered.append(dict(persona))
    st.caption(f"Dashboard is using {len(filtered)} of {len(personas)} personas.")
    return filtered


def _counter_frame(counter: Counter[str], label: str, value_label: str = "Count") -> pd.DataFrame:
    return pd.DataFrame([{label: key, value_label: value} for key, value in counter.most_common()])


def _field_counts(personas: Sequence[Mapping[str, Any]], field: str) -> pd.DataFrame:
    counter = Counter(str(persona.get(field, "Not provided")) for persona in personas)
    return _counter_frame(counter, field.replace("_", " ").title())


def _behavior_distribution(personas: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    for persona in personas:
        behavior = persona_value(persona, "behavior_pattern", {})
        if isinstance(behavior, Mapping):
            counter.update(str(item) for item in behavior.values() if str(item).strip())
        else:
            counter.update(as_list(behavior))
    return _counter_frame(counter, "Behavior")


def _render_gauge(title: str, value: float) -> None:
    st.plotly_chart(
        go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=max(0, min(100, value)),
                number={"suffix": " / 100"},
                title={"text": title},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#2563eb"},
                    "steps": [
                        {"range": [0, 45], "color": "#fee2e2"},
                        {"range": [45, 70], "color": "#fef3c7"},
                        {"range": [70, 100], "color": "#dcfce7"},
                    ],
                },
            )
        ),
        use_container_width=True,
    )


def _render_radar(personas: Sequence[Mapping[str, Any]]) -> None:
    traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
    averages: list[float] = []
    for trait in traits:
        values = []
        for persona in personas:
            big_five = persona.get("big_five_personality") or persona.get("big_five") or {}
            if isinstance(big_five, Mapping):
                values.append(_score(big_five.get(trait)))
        averages.append(round(sum(values) / len(values), 2) if values else 0)
    st.plotly_chart(
        go.Figure(
            data=go.Scatterpolar(r=averages + [averages[0]], theta=[trait.title() for trait in traits] + ["Openness"], fill="toself")
        ).update_layout(title="Persona Psychology Radar", polar={"radialaxis": {"visible": True, "range": [0, 100]}}),
        use_container_width=True,
    )


def _render_word_cloud(insights: Mapping[str, Any] | None, personas: Sequence[Mapping[str, Any]]) -> None:
    keywords = []
    if insights:
        keywords = [
            (str(item.get("keyword", "")), int(item.get("count", 1)))
            for item in insights.get("keywords", [])
            if isinstance(item, Mapping)
        ]
    if not keywords:
        counter: Counter[str] = Counter()
        for persona in personas:
            counter.update(word.lower() for pain in as_list(persona.get("pain_points")) for word in pain.split() if len(word) > 3)
        keywords = counter.most_common(18)
    if not keywords:
        st.info("No keywords available for the word cloud.")
        return

    xs = []
    ys = []
    sizes = []
    labels = []
    max_count = max(count for _, count in keywords) or 1
    for index, (label, count) in enumerate(keywords[:24]):
        angle = index * 0.9
        radius = 0.35 + (index % 5) * 0.14
        xs.append(math.cos(angle) * radius)
        ys.append(math.sin(angle) * radius)
        sizes.append(16 + (count / max_count) * 28)
        labels.append(label.title())
    fig = go.Figure(go.Scatter(x=xs, y=ys, text=labels, mode="text", textfont={"size": sizes, "color": "#0f172a"}))
    fig.update_layout(title="Word Cloud", xaxis={"visible": False}, yaxis={"visible": False}, height=360, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)


def _render_executive_summary(
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    insights: Mapping[str, Any] | None,
    average_age: float,
) -> None:
    product = experiment.get("product_name", "the product")
    product_fit = float((insights or {}).get("product_fit_score") or (survey_results or {}).get("product_fit_score", 0) or 0)
    recommendation = float((insights or {}).get("recommendation_score") or (insights or {}).get("would_use_product_score", 0) or 0)
    summary = (insights or {}).get("product_feedback") or "Generate survey responses and insights to complete the executive summary."
    st.subheader("Executive Summary")
    st.write(
        f"{product} has been evaluated with {len(personas)} synthetic personas with an average age of {average_age}. "
        f"Current product fit is {product_fit:.1f}/100 and recommendation score is {recommendation:.1f}/100. {summary}"
    )


def main() -> None:
    st.set_page_config(page_title="Dashboard", layout="wide")
    init_session_state()
    render_sidebar("Dashboard")
    render_page_header("Dashboard", "Executive analytics from personas, surveys, interviews, and extracted insights.")

    personas = require_personas()
    if personas is None:
        return

    filtered_personas = _filter_personas(personas)
    experiment = get_experiment()
    survey_results = get_survey_results()
    interview_rows = get_interview_results()
    insights = get_insights()
    persona_df = persona_dataframe(filtered_personas)
    age_values = [value for value in persona_df["age"].dropna().tolist()] if not persona_df.empty else []
    average_age = round(sum(age_values) / len(age_values), 1) if age_values else 0
    product_fit = float((insights or {}).get("product_fit_score") or (survey_results or {}).get("product_fit_score", 0) or 0)
    recommendation_score = float((insights or {}).get("recommendation_score") or (insights or {}).get("would_use_product_score", 0) or 0)
    persona_quality = round(float(persona_df["quality_score"].mean()), 1) if not persona_df.empty else 0

    _render_executive_summary(experiment, filtered_personas, survey_results, insights, average_age)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Total Personas", len(filtered_personas))
    metric_col2.metric("Average Age", average_age)
    metric_col3.metric("Product Fit", f"{product_fit:.1f} / 100" if survey_results or insights else "Pending")
    metric_col4.metric("Recommendation", f"{recommendation_score:.1f} / 100" if insights else "Pending")
    metric_col5, metric_col6, metric_col7, metric_col8 = st.columns(4)
    metric_col5.metric("Persona Quality", f"{persona_quality:.1f} / 100")
    metric_col6.metric("Survey Responses", len((survey_results or {}).get("responses", [])))
    metric_col7.metric("Interview Messages", len(interview_rows))
    metric_col8.metric("Insight Confidence", f"{float((insights or {}).get('product_fit_confidence_score', 0) or 0):.0f}" if insights else "Pending")

    with st.expander("Experiment Overview", expanded=True):
        st.json(experiment or {"status": "No experiment metadata available."})

    persona_tab, survey_tab, interview_tab, insight_tab, export_tab = st.tabs(
        ["Persona Analytics", "Survey Analytics", "Interview Analytics", "Insight Analytics", "Export"]
    )

    with persona_tab:
        if persona_df.empty:
            st.info("No persona rows match the current filters.")
        else:
            dist_col1, dist_col2 = st.columns(2)
            with dist_col1:
                st.plotly_chart(px.pie(_field_counts(filtered_personas, "gender"), names="Gender", values="Count", title="Gender Distribution"), use_container_width=True)
                st.plotly_chart(px.bar(_field_counts(filtered_personas, "education"), x="Education", y="Count", title="Education Distribution"), use_container_width=True)
                st.plotly_chart(px.bar(_field_counts(filtered_personas, "technology_usage"), x="Technology Usage", y="Count", title="Technology Usage"), use_container_width=True)
            with dist_col2:
                st.plotly_chart(px.bar(_field_counts(filtered_personas, "occupation"), x="Occupation", y="Count", title="Occupation Distribution"), use_container_width=True)
                st.plotly_chart(px.pie(_field_counts(filtered_personas, "income"), names="Income", values="Count", title="Income Distribution"), use_container_width=True)
                behavior_frame = _behavior_distribution(filtered_personas)
                if not behavior_frame.empty:
                    st.plotly_chart(px.bar(behavior_frame.head(10), x="Count", y="Behavior", orientation="h", title="Behavior Distribution"), use_container_width=True)

            quality_cols = st.columns(2)
            with quality_cols[0]:
                st.plotly_chart(
                    px.bar(
                        persona_df,
                        x="name",
                        y=["quality_score", "diversity_score", "validation_score", "completeness_score", "consistency_score"],
                        barmode="group",
                        title="Persona Quality Score Breakdown",
                    ),
                    use_container_width=True,
                )
            with quality_cols[1]:
                _render_radar(filtered_personas)
            st.dataframe(persona_df, use_container_width=True, hide_index=True)

    analytics: Dict[str, Any] | None = None
    with survey_tab:
        if survey_results and survey_results.get("responses"):
            responses_df = pd.DataFrame(survey_results["responses"])
            analytics = build_dashboard_payload(
                survey_results["responses"],
                personas=filtered_personas,
                product_name=survey_results.get("product_name", experiment.get("product_name", "")),
                research_goal=survey_results.get("research_goal", experiment.get("research_objective", "")),
            )
            survey_analytics = survey_results.get("analytics", {})
            gauge_col, trend_col = st.columns(2)
            with gauge_col:
                _render_gauge("Product Fit Gauge", product_fit)
            with trend_col:
                question_frame = pd.DataFrame(
                    [{"Question": key, "Average Score": value} for key, value in survey_analytics.get("average_by_question", {}).items()]
                )
                if not question_frame.empty:
                    st.plotly_chart(px.line(question_frame, x="Question", y="Average Score", markers=True, title="Question Trend Chart"), use_container_width=True)

            survey_col1, survey_col2 = st.columns(2)
            with survey_col1:
                category_frame = pd.DataFrame(
                    [{"Category": key, "Average Score": value} for key, value in survey_analytics.get("average_by_category", {}).items()]
                )
                if not category_frame.empty:
                    st.plotly_chart(px.bar(category_frame, x="Category", y="Average Score", title="Survey Analytics by Category"), use_container_width=True)
            with survey_col2:
                sentiment_frame = pd.DataFrame(
                    [{"Sentiment": key.title(), "Count": value} for key, value in survey_analytics.get("sentiment_distribution", {}).items()]
                )
                if not sentiment_frame.empty:
                    st.plotly_chart(px.pie(sentiment_frame, names="Sentiment", values="Count", title="Survey Sentiment Chart"), use_container_width=True)
            st.dataframe(responses_df, use_container_width=True, hide_index=True)
        else:
            st.info("Run the survey to populate survey analytics.")
            st.page_link("pages/survey.py", label="Open Survey")

    with interview_tab:
        if interview_rows:
            interview_df = pd.DataFrame(interview_rows)
            persona_counts = interview_df.groupby("persona_name").size().reset_index(name="Messages")
            interview_col1, interview_col2 = st.columns(2)
            with interview_col1:
                st.plotly_chart(px.bar(persona_counts, x="persona_name", y="Messages", title="Interview Messages by Persona"), use_container_width=True)
            with interview_col2:
                emotion_counts = interview_df[interview_df["role"] == "persona"]["emotional_state"].fillna("neutral").value_counts().reset_index()
                emotion_counts.columns = ["Emotional State", "Count"]
                st.plotly_chart(px.pie(emotion_counts, names="Emotional State", values="Count", title="Persona Emotional State"), use_container_width=True)
            if "timestamp" in interview_df.columns:
                trend_df = interview_df.copy()
                trend_df["timestamp"] = pd.to_datetime(trend_df["timestamp"], errors="coerce")
                trend_df = trend_df.dropna(subset=["timestamp"]).sort_values("timestamp")
                if not trend_df.empty:
                    trend_df["Message Count"] = range(1, len(trend_df) + 1)
                    st.plotly_chart(px.line(trend_df, x="timestamp", y="Message Count", color="persona_name", title="Interview Trend Chart"), use_container_width=True)
            st.dataframe(interview_df, use_container_width=True, hide_index=True)
        else:
            st.info("Conduct persona interviews to populate interview analytics.")
            st.page_link("pages/interview.py", label="Open Interview")

    with insight_tab:
        if insights:
            insight_col1, insight_col2 = st.columns(2)
            with insight_col1:
                theme_df = pd.DataFrame(insights.get("themes", []))
                if not theme_df.empty:
                    st.plotly_chart(px.bar(theme_df, x="theme", y="count", title="Theme Charts"), use_container_width=True)
                sentiment_distribution = insights.get("sentiment_distribution", {})
                sentiment_df = pd.DataFrame(
                    [
                        {"Sentiment": key.title(), "Count": value.get("count", 0)}
                        for key, value in sentiment_distribution.items()
                        if isinstance(value, Mapping)
                    ]
                )
                if not sentiment_df.empty:
                    st.plotly_chart(px.pie(sentiment_df, names="Sentiment", values="Count", title="Sentiment Charts"), use_container_width=True)
            with insight_col2:
                _render_gauge("Recommendation Score", recommendation_score)
                _render_word_cloud(insights, filtered_personas)

            st.subheader("AI Recommendations")
            for item in insights.get("final_ai_recommendations", []):
                if isinstance(item, Mapping):
                    st.write(f"- {item.get('recommendation', '')} _(confidence {item.get('confidence_score', 0)})_")
                else:
                    st.write(f"- {item}")

            adopter_df = pd.DataFrame(insights.get("early_adopter_detection", []))
            if not adopter_df.empty:
                st.plotly_chart(px.bar(adopter_df, x="persona", y="score", color="segment", title="Early Adopter Detection"), use_container_width=True)
            with st.expander("Full insight payload", expanded=False):
                st.json(insights)
        else:
            st.info("Extract insights to complete the research dashboard.")
            st.page_link("pages/insights.py", label="Open Insights")

    with export_tab:
        st.subheader("Download Report")
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            st.download_button(
                "Download JSON report",
                data=build_report_download(
                    experiment=experiment,
                    personas=filtered_personas,
                    survey_results=survey_results,
                    interview_rows=interview_rows,
                    insights=insights,
                    analytics=analytics,
                ),
                file_name="synthetic_user_report.json",
                mime="application/json",
                use_container_width=True,
            )
        with export_col2:
            pdf_bytes = export_full_research_report_pdf(
                experiment=experiment,
                personas=filtered_personas,
                survey_results=survey_results,
                interview_rows=interview_rows,
                insights=insights,
            )
            st.download_button(
                "Download PDF report",
                data=pdf_bytes,
                file_name="synthetic_user_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
