from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.services.survey_service import build_dashboard_payload, export_research_report_pdf

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
    }
    .header-card {
        border: 1px solid #dbeafe;
        border-radius: 20px;
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        padding: 1.25rem 1.35rem;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
        margin-bottom: 1.3rem;
    }
    .page-title {
        margin: 0;
        color: #0f172a;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .page-subtitle {
        margin: 0.35rem 0 0;
        color: #475569;
        font-size: 0.98rem;
    }
    .timestamp-pill {
        border: 1px solid #cbd5e1;
        border-radius: 14px;
        background: #fff;
        padding: 0.9rem 1rem;
        text-align: right;
    }
    .timestamp-label {
        display: block;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748b;
    }
    .timestamp-value {
        display: block;
        margin-top: 0.25rem;
        font-size: 0.95rem;
        font-weight: 700;
        color: #0f172a;
    }
    .kpi-card {
        border: 1px solid #dbeafe;
        border-radius: 18px;
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        padding: 1.1rem;
        height: 100%;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
    }
    .kpi-icon {
        font-size: 1.45rem;
        margin-bottom: 0.45rem;
    }
    .kpi-label {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-top: 0.35rem;
        line-height: 1.1;
    }
    .kpi-subtitle {
        font-size: 0.84rem;
        color: #475569;
        margin-top: 0.25rem;
    }
    .section-card {
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        background: #ffffff;
        padding: 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    }
    .section-title {
        margin: 0 0 0.8rem;
        color: #0f172a;
        font-size: 1.05rem;
        font-weight: 800;
    }
    .sidebar .block-container {
        padding-top: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

survey_result = st.session_state.get("survey_results")
personas = st.session_state.get("personas") or st.session_state.get("persona_cards") or st.session_state.get("persona")

if not survey_result or not survey_result.get("responses"):
    st.info("Run a survey from the Survey page or generate a demo dataset before opening the analytics dashboard.")
    st.stop()

responses = survey_result["responses"]
responses_df = pd.DataFrame(responses)

analytics = build_dashboard_payload(
    responses,
    personas=personas if isinstance(personas, list) else [personas] if personas else [],
    product_name=survey_result.get("product_name", ""),
    research_goal=survey_result.get("research_goal", ""),
)

research_report = analytics["research_report"]
insights = analytics["insights"]

header_col, timestamp_col = st.columns([4, 1.05])
with header_col:
    st.markdown(
        """
        <div class="header-card">
            <h1 class="page-title">📊 Analytics Dashboard</h1>
            <p class="page-subtitle">A presentation-ready research workspace for survey performance, persona patterns, and product-fit analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with timestamp_col:
    st.markdown(
        f"""
        <div class="header-card timestamp-pill">
            <span class="timestamp-label">Last Updated</span>
            <span class="timestamp-value">{datetime.now().strftime('%b %d, %Y · %H:%M')}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not responses_df.empty:
    responses_df = responses_df.astype({"score": float})
    responses_df = responses_df.fillna("Not provided")

    if "persona_gender" in responses_df.columns:
        gender_options = ["All"] + sorted(responses_df["persona_gender"].dropna().unique().tolist())
    else:
        gender_options = ["All"]

    if "persona_occupation" in responses_df.columns:
        occupation_options = ["All"] + sorted(responses_df["persona_occupation"].dropna().unique().tolist())
    else:
        occupation_options = ["All"]

    if "persona_age" in responses_df.columns:
        age_values = []
        for item in responses_df["persona_age"]:
            if isinstance(item, str):
                digits = [int(value) for value in item.split() if value.isdigit()]
                if digits:
                    age_values.append(min(digits))
        age_min = min(age_values) if age_values else 18
        age_max = max(age_values) if age_values else 65
    else:
        age_min, age_max = 18, 65

    survey_filter_options = ["All"] + sorted(responses_df["question_id"].dropna().unique().tolist())
    tech_options = ["All"] + sorted(responses_df["persona_technology_usage"].dropna().unique().tolist())
    buying_options = ["All"] + sorted(responses_df["persona_buying_behaviour"].dropna().unique().tolist())

    with st.sidebar:
        st.markdown("### Dashboard Filters")
        selected_gender = st.selectbox("Gender", gender_options)
        selected_occupation = st.selectbox("Occupation", occupation_options)
        selected_survey = st.selectbox("Survey", survey_filter_options)
        selected_tech = st.selectbox("Technology Preference", tech_options)
        selected_buying = st.selectbox("Buying Behaviour", buying_options)
        age_range = st.slider("Age Range", min_value=age_min, max_value=age_max, value=(age_min, age_max))

    filtered_df = responses_df.copy()
    if selected_gender != "All":
        filtered_df = filtered_df[filtered_df["persona_gender"] == selected_gender]
    if selected_occupation != "All":
        filtered_df = filtered_df[filtered_df["persona_occupation"] == selected_occupation]
    if selected_survey != "All":
        filtered_df = filtered_df[filtered_df["question_id"] == selected_survey]
    if selected_tech != "All":
        filtered_df = filtered_df[filtered_df["persona_technology_usage"] == selected_tech]
    if selected_buying != "All":
        filtered_df = filtered_df[filtered_df["persona_buying_behaviour"] == selected_buying]

    def extract_age(value: Any) -> int | None:
        if not isinstance(value, str):
            return None
        digits = [int(x) for x in value.split() if x.isdigit()]
        return min(digits) if digits else None

    filtered_df["age_numeric"] = filtered_df["persona_age"].map(extract_age)
    filtered_df = filtered_df.dropna(subset=["age_numeric"])
    filtered_df = filtered_df[(filtered_df["age_numeric"] >= age_range[0]) & (filtered_df["age_numeric"] <= age_range[1])]

    if filtered_df.empty:
        st.warning("No records match the selected dashboard filters.")
        st.stop()

    total_personas = filtered_df["persona_id"].nunique()
    surveys_executed = filtered_df["question_id"].nunique()
    average_fit = round(filtered_df["score"].mean(), 2) if "score" in filtered_df.columns else 0.0
    average_age = round(filtered_df["age_numeric"].mean(), 2)
    average_satisfaction = average_fit
    dominant_persona_type = filtered_df["persona_occupation"].mode().iloc[0] if not filtered_df["persona_occupation"].empty else "Not available"

    st.markdown("<div class='section-title'>Executive KPI Summary</div>", unsafe_allow_html=True)
    kpi_cols = st.columns(4)
    kpi_items = [
        ("👥", "Total Personas", str(total_personas), "Unique people in the current view"),
        ("📝", "Total Survey Responses", str(filtered_df.shape[0]), "Responses available after filtering"),
        ("📈", "Product Fit Score", f"{average_fit:.1f}%", "Weighted compatibility score"),
        ("😊", "Average Satisfaction", f"{average_satisfaction:.1f}%", "Average sentiment score"),
    ]

    for col, (icon, label, value, subtitle) in zip(kpi_cols, kpi_items):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-subtitle">{subtitle}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div class='section-title' style='margin-top: 1.5rem;'>Professional Analytics</div>", unsafe_allow_html=True)

    persona_distribution = filtered_df["persona_gender"].fillna("Unknown").value_counts().reset_index()
    persona_distribution.columns = ["Gender", "Count"]

    if isinstance(personas, list):
        pain_counter: Counter[str] = Counter()
        for persona in personas:
            if not isinstance(persona, dict):
                continue
            for pain_point in persona.get("pain_points", []):
                pain_counter[str(pain_point).strip()] += 1
        pain_df = pd.DataFrame(pain_counter.most_common(6), columns=["Pain Point", "Count"])
    else:
        pain_df = pd.DataFrame(columns=["Pain Point", "Count"])

    trend_df = filtered_df.copy()
    if "timestamp" in trend_df.columns:
        trend_df["timestamp"] = pd.to_datetime(trend_df["timestamp"], errors="coerce")
        trend_df = trend_df.dropna(subset=["timestamp"])
        trend_df = trend_df.groupby(trend_df["timestamp"].dt.floor("h"))["score"].mean().reset_index(name="avg_score")
        trend_df.columns = ["Time", "Product Fit"]
    else:
        trend_df = pd.DataFrame(columns=["Time", "Product Fit"])

    survey_rating_df = filtered_df.groupby("question_id")["score"].mean().reset_index(name="avg_score")
    survey_rating_df.columns = ["Question", "Average Score"]

    heatmap_df = filtered_df.pivot_table(index="persona_name", columns="question_id", values="score", aggfunc="mean")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        with st.container():
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            persona_pie = px.pie(
                persona_distribution,
                names="Gender",
                values="Count",
                title="Persona Distribution",
                hole=0.48,
            )
            persona_pie.update_layout(
                title_x=0.5,
                paper_bgcolor="white",
                plot_bgcolor="white",
                legend_title_text="Gender",
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(persona_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with chart_col2:
        with st.container():
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            if pain_df.empty:
                st.info("No top pain point data is available for this filtered view.")
            else:
                pain_chart = px.bar(
                    pain_df.sort_values("Count", ascending=True),
                    x="Count",
                    y="Pain Point",
                    orientation="h",
                    color="Pain Point",
                    title="Top Pain Points",
                )
                pain_chart.update_layout(
                    title_x=0.5,
                    xaxis_title="Count",
                    yaxis_title="Pain Point",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    legend_title_text="Pain Point",
                    margin=dict(l=20, r=20, t=50, b=20),
                )
                st.plotly_chart(pain_chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        with st.container():
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            if trend_df.empty:
                st.info("Product fit trend is not available for the selected slice.")
            else:
                line_chart = px.line(
                    trend_df,
                    x="Time",
                    y="Product Fit",
                    markers=True,
                    title="Product Fit Trend",
                )
                line_chart.update_layout(
                    title_x=0.5,
                    xaxis_title="Time",
                    yaxis_title="Average Product Fit",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    legend_title_text="Trend",
                    margin=dict(l=20, r=20, t=50, b=20),
                )
                st.plotly_chart(line_chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with chart_col4:
        with st.container():
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            rating_chart = px.bar(
                survey_rating_df,
                x="Question",
                y="Average Score",
                color="Question",
                title="Survey Ratings",
            )
            rating_chart.update_layout(
                title_x=0.5,
                xaxis_title="Question",
                yaxis_title="Average Score",
                plot_bgcolor="white",
                paper_bgcolor="white",
                legend_title_text="Question",
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(rating_chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if not heatmap_df.empty and heatmap_df.shape[0] > 1 and heatmap_df.shape[1] > 1:
        st.markdown("<div class='section-title' style='margin-top: 1.5rem;'>Response Heatmap</div>", unsafe_allow_html=True)
        heatmap_fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_df.values,
                x=heatmap_df.columns,
                y=heatmap_df.index,
                colorscale="Viridis",
                hovertemplate="Persona: %{y}<br>Question: %{x}<br>Score: %{z:.1f}<extra></extra>",
            )
        )
        heatmap_fig.update_layout(
            title="Survey Response Heatmap",
            title_x=0.5,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis_title="Question",
            yaxis_title="Persona",
        )
        st.plotly_chart(heatmap_fig, use_container_width=True)

    st.markdown("<div class='section-title' style='margin-top: 1.5rem;'>Product Fit Analysis</div>", unsafe_allow_html=True)
    fit_details = []
    for response in filtered_df.to_dict("records"):
        details = response.get("product_fit_details") or {}
        if isinstance(details, dict):
            fit_details.append(details)

    if fit_details:
        overall_scores = [item.get("overall_score", 0.0) for item in fit_details]
        average_score = round(sum(overall_scores) / len(overall_scores), 2)
        st.metric("Overall Compatibility", f"{average_score:.1f} / 100")

        category_aggregate: Dict[str, List[float]] = {}
        for item in fit_details:
            for category, score in (item.get("category_scores") or {}).items():
                category_aggregate.setdefault(category, []).append(float(score))

        fit_frame = pd.DataFrame(
            {"Category": [key for key in category_aggregate], "Average Score": [round(sum(values) / len(values), 2) for values in category_aggregate.values()]}
        )
        fit_chart = px.bar(fit_frame, x="Category", y="Average Score", color="Category", title="Category-wise Compatibility")
        fit_chart.update_layout(showlegend=False, paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fit_chart, use_container_width=True)

        for item in fit_details:
            with st.expander("Compatibility Details"):
                st.json(item)

    st.markdown("<div class='section-title' style='margin-top: 1.5rem;'>Insight Extraction</div>", unsafe_allow_html=True)
    for insight in insights[:5]:
        with st.expander(insight.get("question", "Insight")):
            st.write(insight.get("readable_summary", insight.get("insight", "")))

    st.markdown("<div class='section-title' style='margin-top: 1.5rem;'>Executive Research Summary</div>", unsafe_allow_html=True)
    summary = research_report.get("research_overview", {})
    st.write("### Research Overview")
    col_a, col_b = st.columns(2)
    with col_a:
        st.json(summary)
    with col_b:
        st.json(research_report.get("persona_summary", {}))

    st.write("### Key Insights")
    st.write("\n".join(research_report.get("key_insights", [])))

    st.write("### Final Recommendation")
    st.write(research_report.get("final_recommendation", "No recommendation available."))

    st.markdown("---")

    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    json_bytes = json.dumps(filtered_df.to_dict("records"), indent=2).encode("utf-8")
    report_pdf = export_research_report_pdf(research_report)

    st.markdown("<div class='section-title'>Export Section</div>", unsafe_allow_html=True)
    export_col1, export_col2, export_col3 = st.columns(3)
    with export_col1:
        st.download_button(
            label="Export CSV",
            data=csv_bytes,
            file_name="filtered_dashboard_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with export_col2:
        st.download_button(
            label="Export JSON",
            data=json_bytes,
            file_name="filtered_dashboard_results.json",
            mime="application/json",
            use_container_width=True,
        )
    with export_col3:
        st.download_button(
            label="Export PDF Report",
            data=report_pdf,
            file_name="research_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
