from __future__ import annotations

import json
import re
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
    """Safely convert a score-like value to a float."""
    if value in (None, ""):
        return 0.0

    try:
        return float(str(value).replace("%", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert arbitrary values to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _chart_config() -> dict[str, Any]:
    """Common Plotly configuration for a clean dashboard."""
    return {
        "displayModeBar": False,
        "responsive": True,
    }


def persona_dataframe(
    personas: Sequence[Mapping[str, Any]],
) -> pd.DataFrame:
    """Convert persona dictionaries into a dashboard-friendly DataFrame."""
    rows: list[dict[str, Any]] = []

    for persona in personas:
        behavior = persona_value(
            persona,
            "behavior_pattern",
            {},
        )

        if isinstance(behavior, Mapping):
            behavior_summary = ", ".join(
                str(item)
                for item in behavior.values()
                if str(item).strip()
            )
        else:
            behavior_summary = ", ".join(
                as_list(behavior)
            )

        rows.append(
            {
                "name": persona.get(
                    "name",
                    "Unknown",
                ),
                "age": age_number(
                    persona.get("age")
                ),
                "gender": persona.get(
                    "gender",
                    "Not provided",
                ),
                "occupation": persona.get(
                    "occupation",
                    "Not provided",
                ),
                "education": persona.get(
                    "education",
                    "Not provided",
                ),
                "income": persona.get(
                    "income",
                    "Not provided",
                ),
                "technology_usage": persona.get(
                    "technology_usage",
                    "Not provided",
                ),
                "buying_behavior": (
                    persona.get("buying_behavior")
                    or persona.get("buying_behaviour")
                    or "Not provided"
                ),
                "behavior": (
                    behavior_summary
                    or "Not provided"
                ),
                "quality_score": _score(
                    persona.get("quality_score")
                ),
                "diversity_score": _score(
                    persona.get("diversity_score")
                ),
                "validation_score": _score(
                    persona.get("validation_score")
                ),
                "completeness_score": _score(
                    persona.get("completeness_score")
                ),
                "consistency_score": _score(
                    persona.get("consistency_score")
                ),
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
    """Build a portable JSON research report."""
    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "experiment": dict(experiment),
        "personas": [
            dict(persona)
            for persona in personas
        ],
        "survey_results": dict(
            survey_results or {}
        ),
        "interview_results": [
            dict(row)
            for row in interview_rows
        ],
        "insights": dict(
            insights or {}
        ),
        "analytics": dict(
            analytics or {}
        ),
    }

    return json.dumps(
        report,
        indent=2,
        default=str,
    ).encode("utf-8")


def _filter_personas(
    personas: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Apply dashboard filters without changing session-state personas."""
    frame = persona_dataframe(personas)

    if frame.empty:
        return [
            dict(persona)
            for persona in personas
        ]

    st.subheader("Interactive Filters")

    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(
        [1.5, 1, 1, 1]
    )

    with filter_col1:
        search = st.text_input(
            "Search",
            placeholder=(
                "Name, occupation, behavior, or segment"
            ),
        )

    with filter_col2:
        occupation_options = [
            "All"
        ] + sorted(
            frame["occupation"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        occupation = st.selectbox(
            "Occupation",
            occupation_options,
        )

    with filter_col3:
        education_options = [
            "All"
        ] + sorted(
            frame["education"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        education = st.selectbox(
            "Education",
            education_options,
        )

    with filter_col4:
        technology_options = [
            "All"
        ] + sorted(
            frame["technology_usage"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        technology = st.selectbox(
            "Technology",
            technology_options,
        )

    filtered: list[dict[str, Any]] = []
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

        if (
            occupation != "All"
            and str(
                persona.get(
                    "occupation",
                    "Not provided",
                )
            )
            != occupation
        ):
            continue

        if (
            education != "All"
            and str(
                persona.get(
                    "education",
                    "Not provided",
                )
            )
            != education
        ):
            continue

        if (
            technology != "All"
            and str(
                persona.get(
                    "technology_usage",
                    "Not provided",
                )
            )
            != technology
        ):
            continue

        filtered.append(dict(persona))

    st.caption(
        f"Dashboard is using {len(filtered)} "
        f"of {len(personas)} personas."
    )

    return filtered


def _counter_frame(
    counter: Counter[str],
    label: str,
    value_label: str = "Count",
) -> pd.DataFrame:
    """Convert a Counter to a DataFrame."""
    return pd.DataFrame(
        [
            {
                label: key,
                value_label: value,
            }
            for key, value in counter.most_common()
        ]
    )


def _field_counts(
    personas: Sequence[Mapping[str, Any]],
    field: str,
) -> pd.DataFrame:
    counter = Counter(
        str(
            persona.get(
                field,
                "Not provided",
            )
        )
        for persona in personas
    )

    return _counter_frame(
        counter,
        field.replace("_", " ").title(),
    )


def _behavior_distribution(
    personas: Sequence[Mapping[str, Any]],
) -> pd.DataFrame:
    counter: Counter[str] = Counter()

    for persona in personas:
        behavior = persona_value(
            persona,
            "behavior_pattern",
            {},
        )

        if isinstance(behavior, Mapping):
            counter.update(
                str(item)
                for item in behavior.values()
                if str(item).strip()
            )
        else:
            counter.update(
                as_list(behavior)
            )

    return _counter_frame(
        counter,
        "Behavior",
    )


def _render_gauge(
    title: str,
    value: float,
) -> None:
    """Render a compact, readable 0-100 gauge."""
    value = max(
        0.0,
        min(100.0, _safe_float(value)),
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={
                "suffix": " / 100",
                "font": {
                    "size": 38,
                },
            },
            title={
                "text": title,
                "font": {
                    "size": 19,
                },
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickmode": "linear",
                    "tick0": 0,
                    "dtick": 20,
                    "tickfont": {
                        "size": 11,
                    },
                },
                "bar": {
                    "color": "#2563eb",
                    "thickness": 0.32,
                },
                "steps": [
                    {
                        "range": [0, 45],
                        "color": "#fee2e2",
                    },
                    {
                        "range": [45, 70],
                        "color": "#fef3c7",
                    },
                    {
                        "range": [70, 100],
                        "color": "#dcfce7",
                    },
                ],
                "threshold": {
                    "line": {
                        "color": "#1d4ed8",
                        "width": 3,
                    },
                    "thickness": 0.72,
                    "value": value,
                },
            },
        )
    )

    fig.update_layout(
        height=330,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=_chart_config(),
    )


def _render_radar(
    personas: Sequence[Mapping[str, Any]],
) -> None:
    """Render average Big Five personality traits."""
    traits = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
    ]

    averages: list[float] = []

    for trait in traits:
        values: list[float] = []

        for persona in personas:
            big_five = (
                persona.get(
                    "big_five_personality"
                )
                or persona.get("big_five")
                or {}
            )

            if isinstance(big_five, Mapping):
                values.append(
                    _score(
                        big_five.get(trait)
                    )
                )

        averages.append(
            round(
                sum(values) / len(values),
                2,
            )
            if values
            else 0.0
        )

    closed_values = averages + (
        [averages[0]]
        if averages
        else [0.0]
    )

    closed_traits = [
        trait.title()
        for trait in traits
    ] + ["Openness"]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=closed_values,
            theta=closed_traits,
            fill="toself",
            name="Average",
        )
    )

    fig.update_layout(
        title="Persona Psychology Radar",
        height=360,
        margin=dict(
            l=30,
            r=30,
            t=60,
            b=30,
        ),
        polar={
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {
                    "size": 10,
                },
            }
        },
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=_chart_config(),
    )


def _render_word_cloud(
    insights: Mapping[str, Any] | None,
    personas: Sequence[Mapping[str, Any]],
) -> None:
    """
    Render a collision-free keyword visualization.

    A treemap is intentionally used instead of manually positioning
    words, because manual text coordinates cause overlapping labels
    on different screen sizes.
    """
    keywords: list[tuple[str, int]] = []

    if insights:
        raw_keywords = insights.get(
            "keywords",
            [],
        )

        if isinstance(raw_keywords, list):
            for item in raw_keywords:
                if not isinstance(item, Mapping):
                    continue

                keyword = str(
                    item.get(
                        "keyword",
                        "",
                    )
                ).strip()

                if not keyword:
                    continue

                try:
                    count = int(
                        item.get(
                            "count",
                            1,
                        )
                    )
                except (
                    ValueError,
                    TypeError,
                ):
                    count = 1

                keywords.append(
                    (
                        keyword,
                        max(1, count),
                    )
                )

    if not keywords:
        counter: Counter[str] = Counter()

        stop_words = {
            "this",
            "that",
            "with",
            "from",
            "have",
            "they",
            "their",
            "very",
            "more",
            "some",
            "would",
            "could",
            "about",
            "into",
            "because",
            "product",
            "products",
            "user",
            "users",
            "persona",
            "personas",
            "using",
            "used",
            "make",
            "makes",
            "need",
            "needs",
        }

        for persona in personas:
            pain_points = as_list(
                persona.get(
                    "pain_points"
                )
            )

            for pain in pain_points:
                words = re.findall(
                    r"[A-Za-z]{4,}",
                    str(pain).lower(),
                )

                for word in words:
                    if word not in stop_words:
                        counter[word] += 1

        keywords = counter.most_common(12)

    if not keywords:
        st.info(
            "No keywords available for the research themes."
        )
        return

    word_df = pd.DataFrame(
        keywords,
        columns=[
            "Keyword",
            "Count",
        ],
    )

    word_df["Keyword"] = (
        word_df["Keyword"]
        .astype(str)
        .str.title()
    )

    word_df = (
        word_df
        .sort_values(
            "Count",
            ascending=False,
        )
        .head(12)
    )

    fig = px.treemap(
        word_df,
        path=["Keyword"],
        values="Count",
        title="Key Research Themes",
    )

    fig.update_traces(
        textinfo="label+value",
        textfont={
            "size": 14,
        },
        hovertemplate=(
            "<b>%{label}</b>"
            "<br>Mentions: %{value}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=360,
        margin=dict(
            l=10,
            r=10,
            t=55,
            b=10,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=_chart_config(),
    )


def _render_executive_summary(
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    insights: Mapping[str, Any] | None,
    average_age: float,
) -> None:
    """Render a concise research summary."""
    product = experiment.get(
        "product_name",
        "the product",
    )

    product_fit = _safe_float(
        (
            insights or {}
        ).get(
            "product_fit_score"
        )
        or (
            survey_results or {}
        ).get(
            "product_fit_score",
            0,
        )
    )

    recommendation = _safe_float(
        (
            insights or {}
        ).get(
            "recommendation_score"
        )
        or (
            insights or {}
        ).get(
            "would_use_product_score",
            0,
        )
    )

    summary = (
        insights or {}
    ).get(
        "product_feedback"
    ) or (
        "Generate survey responses and insights "
        "to complete the executive summary."
    )

    st.subheader(
        "Executive Summary"
    )

    st.write(
        f"{product} has been evaluated with "
        f"{len(personas)} synthetic personas "
        f"with an average age of "
        f"{average_age:.1f}. "
        f"Current product fit is "
        f"{product_fit:.1f}/100 and "
        f"recommendation score is "
        f"{recommendation:.1f}/100. "
        f"{summary}"
    )


def _render_persona_analytics(
    filtered_personas: Sequence[Mapping[str, Any]],
    persona_df: pd.DataFrame,
) -> None:
    """Render persona-level analytics."""
    if persona_df.empty:
        st.info(
            "No persona rows match the current filters."
        )
        return

    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
        gender_df = _field_counts(
            filtered_personas,
            "gender",
        )

        if not gender_df.empty:
            fig = px.pie(
                gender_df,
                names="Gender",
                values="Count",
                hole=0.42,
                title="Gender Distribution",
            )
            fig.update_layout(
                height=340,
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=30,
                ),
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

        education_df = _field_counts(
            filtered_personas,
            "education",
        )

        if not education_df.empty:
            fig = px.bar(
                education_df,
                x="Education",
                y="Count",
                title="Education Distribution",
                text="Count",
            )
            fig.update_traces(
                textposition="outside"
            )
            fig.update_layout(
                height=340,
                xaxis={
                    "tickangle": -25,
                    "automargin": True,
                },
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=80,
                ),
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

        technology_df = _field_counts(
            filtered_personas,
            "technology_usage",
        )

        if not technology_df.empty:
            fig = px.bar(
                technology_df,
                x="Count",
                y="Technology Usage",
                orientation="h",
                title="Technology Usage",
                text="Count",
            )
            fig.update_traces(
                textposition="outside"
            )
            fig.update_layout(
                height=360,
                margin=dict(
                    l=20,
                    r=50,
                    t=60,
                    b=30,
                ),
                yaxis={
                    "automargin": True,
                },
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

    with dist_col2:
        occupation_df = _field_counts(
            filtered_personas,
            "occupation",
        )

        if not occupation_df.empty:
            fig = px.bar(
                occupation_df,
                x="Count",
                y="Occupation",
                orientation="h",
                title="Occupation Distribution",
                text="Count",
            )
            fig.update_traces(
                textposition="outside"
            )
            fig.update_layout(
                height=360,
                margin=dict(
                    l=20,
                    r=50,
                    t=60,
                    b=30,
                ),
                yaxis={
                    "automargin": True,
                },
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

        income_df = _field_counts(
            filtered_personas,
            "income",
        )

        if not income_df.empty:
            fig = px.pie(
                income_df,
                names="Income",
                values="Count",
                hole=0.42,
                title="Income Distribution",
            )
            fig.update_layout(
                height=340,
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=30,
                ),
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

        behavior_frame = _behavior_distribution(
            filtered_personas
        )

        if not behavior_frame.empty:
            fig = px.bar(
                behavior_frame.head(10),
                x="Count",
                y="Behavior",
                orientation="h",
                title="Behavior Distribution",
                text="Count",
            )
            fig.update_traces(
                textposition="outside"
            )
            fig.update_layout(
                height=380,
                margin=dict(
                    l=20,
                    r=50,
                    t=60,
                    b=30,
                ),
                yaxis={
                    "automargin": True,
                },
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

    quality_cols = st.columns(2)

    with quality_cols[0]:
        score_columns = [
            "quality_score",
            "diversity_score",
            "validation_score",
            "completeness_score",
            "consistency_score",
        ]

        available_columns = [
            column
            for column in score_columns
            if column in persona_df.columns
        ]

        if available_columns:
            quality_fig = px.bar(
                persona_df,
                x="name",
                y=available_columns,
                barmode="group",
                title="Persona Quality Score Breakdown",
            )

            quality_fig.update_layout(
                height=400,
                xaxis={
                    "tickangle": -25,
                    "automargin": True,
                },
                yaxis={
                    "range": [0, 100],
                    "title": "Score",
                },
                margin=dict(
                    l=30,
                    r=20,
                    t=60,
                    b=90,
                ),
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5,
                },
            )

            st.plotly_chart(
                quality_fig,
                use_container_width=True,
                config=_chart_config(),
            )

    with quality_cols[1]:
        _render_radar(
            filtered_personas
        )

    st.dataframe(
        persona_df,
        use_container_width=True,
        hide_index=True,
    )


def _render_survey_analytics(
    survey_results: Mapping[str, Any] | None,
    filtered_personas: Sequence[Mapping[str, Any]],
    experiment: Mapping[str, Any],
    product_fit: float,
) -> Dict[str, Any] | None:
    """Render survey analytics and return dashboard payload."""
    if not survey_results:
        st.info(
            "Run the survey to populate survey analytics."
        )
        st.page_link(
            "pages/survey.py",
            label="Open Survey",
        )
        return None

    responses = survey_results.get(
        "responses",
        [],
    )

    if not responses:
        st.info(
            "Run the survey to populate survey analytics."
        )
        st.page_link(
            "pages/survey.py",
            label="Open Survey",
        )
        return None

    responses_df = pd.DataFrame(
        responses
    )

    analytics: Dict[str, Any] | None = None

    try:
        analytics = build_dashboard_payload(
            responses,
            personas=filtered_personas,
            product_name=survey_results.get(
                "product_name",
                experiment.get(
                    "product_name",
                    "",
                ),
            ),
            research_goal=survey_results.get(
                "research_goal",
                experiment.get(
                    "research_objective",
                    "",
                ),
            ),
        )
    except Exception as exc:
        st.warning(
            "Advanced survey analytics could not be "
            f"calculated: {exc}"
        )

    survey_analytics = (
        survey_results.get(
            "analytics",
            {},
        )
        or {}
    )

    gauge_col, trend_col = st.columns(2)

    with gauge_col:
        _render_gauge(
            "Product Fit Gauge",
            product_fit,
        )

    with trend_col:
        question_frame = pd.DataFrame(
            [
                {
                    "Question": key,
                    "Average Score": value,
                }
                for key, value in (
                    survey_analytics.get(
                        "average_by_question",
                        {},
                    )
                    or {}
                ).items()
            ]
        )

        if not question_frame.empty:
            question_fig = px.bar(
                question_frame,
                x="Question",
                y="Average Score",
                title="Average Score by Question",
                text="Average Score",
            )

            question_fig.update_traces(
                texttemplate="%{text:.1f}",
                textposition="outside",
            )

            question_fig.update_layout(
                height=360,
                xaxis={
                    "tickangle": -30,
                    "automargin": True,
                },
                yaxis={
                    "range": [0, 100],
                    "automargin": True,
                    "title": "Average Score",
                },
                margin=dict(
                    l=35,
                    r=20,
                    t=60,
                    b=110,
                ),
            )

            st.plotly_chart(
                question_fig,
                use_container_width=True,
                config=_chart_config(),
            )

    survey_col1, survey_col2 = st.columns(2)

    with survey_col1:
        category_frame = pd.DataFrame(
            [
                {
                    "Category": key,
                    "Average Score": value,
                }
                for key, value in (
                    survey_analytics.get(
                        "average_by_category",
                        {},
                    )
                    or {}
                ).items()
            ]
        )

        if not category_frame.empty:
            category_fig = px.bar(
                category_frame,
                x="Category",
                y="Average Score",
                title="Survey Analytics by Category",
                text="Average Score",
            )

            category_fig.update_traces(
                texttemplate="%{text:.1f}",
                textposition="outside",
            )

            category_fig.update_layout(
                height=360,
                xaxis={
                    "tickangle": -25,
                    "automargin": True,
                },
                yaxis={
                    "range": [0, 100],
                },
                margin=dict(
                    l=35,
                    r=20,
                    t=60,
                    b=90,
                ),
            )

            st.plotly_chart(
                category_fig,
                use_container_width=True,
                config=_chart_config(),
            )

    with survey_col2:
        sentiment_frame = pd.DataFrame(
            [
                {
                    "Sentiment": str(
                        key
                    ).title(),
                    "Count": value,
                }
                for key, value in (
                    survey_analytics.get(
                        "sentiment_distribution",
                        {},
                    )
                    or {}
                ).items()
            ]
        )

        if not sentiment_frame.empty:
            sentiment_fig = px.pie(
                sentiment_frame,
                names="Sentiment",
                values="Count",
                hole=0.45,
                title="Survey Sentiment",
            )

            sentiment_fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b>"
                    "<br>Responses: %{value}"
                    "<br>Share: %{percent}"
                    "<extra></extra>"
                ),
            )

            sentiment_fig.update_layout(
                height=360,
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=45,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.18,
                    xanchor="center",
                    x=0.5,
                ),
            )

            st.plotly_chart(
                sentiment_fig,
                use_container_width=True,
                config=_chart_config(),
            )

    st.dataframe(
        responses_df,
        use_container_width=True,
        hide_index=True,
    )

    return analytics


def _render_interview_analytics(
    interview_rows: Sequence[Mapping[str, Any]],
) -> None:
    """Render interview analytics safely."""
    if not interview_rows:
        st.info(
            "Conduct persona interviews to populate interview analytics."
        )
        st.page_link(
            "pages/interview.py",
            label="Open Interview",
        )
        return

    interview_df = pd.DataFrame(
        interview_rows
    )

    if interview_df.empty:
        st.info(
            "No interview records are available."
        )
        return

    if "persona_name" in interview_df.columns:
        persona_counts = (
            interview_df
            .groupby("persona_name")
            .size()
            .reset_index(
                name="Messages"
            )
        )

        interview_col1, interview_col2 = st.columns(2)

        with interview_col1:
            fig = px.bar(
                persona_counts,
                x="persona_name",
                y="Messages",
                title="Interview Messages by Persona",
                text="Messages",
            )
            fig.update_traces(
                textposition="outside"
            )
            fig.update_layout(
                height=360,
                xaxis={
                    "tickangle": -25,
                    "automargin": True,
                },
                margin=dict(
                    l=30,
                    r=20,
                    t=60,
                    b=90,
                ),
            )
            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

        with interview_col2:
            if (
                "role" in interview_df.columns
                and "emotional_state" in interview_df.columns
            ):
                persona_emotions = interview_df[
                    interview_df["role"]
                    .astype(str)
                    .str.lower()
                    .eq("persona")
                ]

                emotion_counts = (
                    persona_emotions[
                        "emotional_state"
                    ]
                    .fillna("neutral")
                    .astype(str)
                    .str.title()
                    .value_counts()
                    .reset_index()
                )

                emotion_counts.columns = [
                    "Emotional State",
                    "Count",
                ]

                if not emotion_counts.empty:
                    fig = px.pie(
                        emotion_counts,
                        names="Emotional State",
                        values="Count",
                        hole=0.45,
                        title="Persona Emotional State",
                    )
                    fig.update_layout(
                        height=360,
                        margin=dict(
                            l=20,
                            r=20,
                            t=60,
                            b=35,
                        ),
                    )
                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                        config=_chart_config(),
                    )

    if "timestamp" in interview_df.columns:
        trend_df = interview_df.copy()
        trend_df["timestamp"] = pd.to_datetime(
            trend_df["timestamp"],
            errors="coerce",
        )
        trend_df = (
            trend_df
            .dropna(
                subset=["timestamp"]
            )
            .sort_values("timestamp")
        )

        if not trend_df.empty:
            trend_df["Message Count"] = range(
                1,
                len(trend_df) + 1,
            )

            color_column = (
                "persona_name"
                if "persona_name"
                in trend_df.columns
                else None
            )

            fig = px.line(
                trend_df,
                x="timestamp",
                y="Message Count",
                color=color_column,
                markers=True,
                title="Interview Trend",
            )

            fig.update_layout(
                height=360,
                margin=dict(
                    l=30,
                    r=30,
                    t=60,
                    b=50,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

    st.dataframe(
        interview_df,
        use_container_width=True,
        hide_index=True,
    )


def _render_insight_analytics(
    insights: Mapping[str, Any] | None,
    filtered_personas: Sequence[Mapping[str, Any]],
    recommendation_score: float,
) -> None:
    """Render insight analytics and recommendations."""
    if not insights:
        st.info(
            "Extract insights to complete the research dashboard."
        )
        st.page_link(
            "pages/insights.py",
            label="Open Insights",
        )
        return

    insight_col1, insight_col2 = st.columns(2)

    with insight_col1:
        theme_df = pd.DataFrame(
            insights.get(
                "themes",
                [],
            )
        )

        if not theme_df.empty:
            if {
                "theme",
                "count",
            }.issubset(theme_df.columns):
                theme_fig = px.bar(
                    theme_df,
                    x="count",
                    y="theme",
                    orientation="h",
                    title="Research Themes",
                    text="count",
                )

                theme_fig.update_traces(
                    textposition="outside"
                )

                theme_fig.update_layout(
                    height=380,
                    xaxis={
                        "title": "Mentions",
                    },
                    yaxis={
                        "categoryorder": (
                            "total ascending"
                        ),
                        "automargin": True,
                    },
                    margin=dict(
                        l=20,
                        r=55,
                        t=60,
                        b=30,
                    ),
                )

                st.plotly_chart(
                    theme_fig,
                    use_container_width=True,
                    config=_chart_config(),
                )

        sentiment_distribution = insights.get(
            "sentiment_distribution",
            {},
        )

        if isinstance(
            sentiment_distribution,
            Mapping,
        ):
            sentiment_df = pd.DataFrame(
                [
                    {
                        "Sentiment": str(
                            key
                        ).title(),
                        "Count": (
                            value.get(
                                "count",
                                0,
                            )
                            if isinstance(
                                value,
                                Mapping,
                            )
                            else value
                        ),
                    }
                    for key, value in (
                        sentiment_distribution
                    ).items()
                ]
            )
        else:
            sentiment_df = pd.DataFrame()

        if not sentiment_df.empty:
            sentiment_fig = px.pie(
                sentiment_df,
                names="Sentiment",
                values="Count",
                hole=0.45,
                title="Sentiment Distribution",
            )

            sentiment_fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b>"
                    "<br>Mentions: %{value}"
                    "<br>Share: %{percent}"
                    "<extra></extra>"
                ),
            )

            sentiment_fig.update_layout(
                height=360,
                margin=dict(
                    l=20,
                    r=20,
                    t=60,
                    b=40,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.18,
                    xanchor="center",
                    x=0.5,
                ),
            )

            st.plotly_chart(
                sentiment_fig,
                use_container_width=True,
                config=_chart_config(),
            )

    with insight_col2:
        _render_gauge(
            "Recommendation Score",
            recommendation_score,
        )

        _render_word_cloud(
            insights,
            filtered_personas,
        )

    st.subheader(
        "AI Recommendations"
    )

    recommendations = insights.get(
        "final_ai_recommendations",
        [],
    )

    if recommendations:
        for item in recommendations:
            if isinstance(item, Mapping):
                recommendation = item.get(
                    "recommendation",
                    "",
                )
                confidence = item.get(
                    "confidence_score",
                    0,
                )
                st.write(
                    f"- {recommendation} "
                    f"_(confidence {confidence})_"
                )
            else:
                st.write(
                    f"- {item}"
                )
    else:
        st.info(
            "No AI recommendations are available yet."
        )

    adopter_df = pd.DataFrame(
        insights.get(
            "early_adopter_detection",
            [],
        )
    )

    if not adopter_df.empty:
        required = {
            "persona",
            "score",
        }

        if required.issubset(
            adopter_df.columns
        ):
            color_column = (
                "segment"
                if "segment"
                in adopter_df.columns
                else None
            )

            fig = px.bar(
                adopter_df,
                x="persona",
                y="score",
                color=color_column,
                title="Early Adopter Detection",
                text="score",
            )

            fig.update_traces(
                texttemplate="%{text:.1f}",
                textposition="outside",
            )

            fig.update_layout(
                height=380,
                xaxis={
                    "tickangle": -25,
                    "automargin": True,
                },
                yaxis={
                    "range": [0, 100],
                    "title": "Score",
                },
                margin=dict(
                    l=30,
                    r=30,
                    t=60,
                    b=90,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                config=_chart_config(),
            )

    with st.expander(
        "Full insight payload",
        expanded=False,
    ):
        st.json(
            insights
        )


def _render_export_tab(
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    insights: Mapping[str, Any] | None,
    analytics: Mapping[str, Any] | None,
) -> None:
    """Render report export and workflow completion."""
    st.subheader(
        "Download Report"
    )

    export_col1, export_col2 = st.columns(2)

    with export_col1:
        json_bytes = build_report_download(
            experiment=experiment,
            personas=personas,
            survey_results=survey_results,
            interview_rows=interview_rows,
            insights=insights,
            analytics=analytics,
        )

        st.download_button(
            "Download JSON Report",
            data=json_bytes,
            file_name=(
                "synthetic_user_report.json"
            ),
            mime="application/json",
            use_container_width=True,
        )

    with export_col2:
        if analytics or insights:
            try:
                pdf_bytes = (
                    export_full_research_report_pdf(
                        experiment=experiment,
                        personas=personas,
                        survey_results=survey_results,
                        interview_rows=interview_rows,
                        insights=insights,
                    )
                )

                st.download_button(
                    "Download PDF Report",
                    data=pdf_bytes,
                    file_name=(
                        "synthetic_user_report.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as exc:
                st.error(
                    "Unable to generate PDF report: "
                    f"{exc}"
                )
        else:
            st.info(
                "Run the survey or extract insights "
                "before generating the PDF report."
            )

    st.divider()

    completion_frame = pd.DataFrame(
        [
            {
                "Stage": "Generated Personas",
                "Complete": len(personas),
            },
            {
                "Stage": "Survey Responses",
                "Complete": len(
                    (
                        survey_results or {}
                    ).get(
                        "responses",
                        [],
                    )
                ),
            },
            {
                "Stage": "Interview Messages",
                "Complete": len(
                    interview_rows
                ),
            },
            {
                "Stage": "Focus Group Turns",
                "Complete": len(
                    st.session_state.get(
                        "focus_group_results",
                        [],
                    )
                ),
            },
        ]
    )

    st.subheader(
        "Research Workflow Completion"
    )

    completion_fig = px.bar(
        completion_frame,
        x="Stage",
        y="Complete",
        title="Workflow Completion",
        text="Complete",
    )

    completion_fig.update_traces(
        textposition="outside"
    )

    completion_fig.update_layout(
        height=360,
        xaxis={
            "tickangle": -20,
            "automargin": True,
        },
        margin=dict(
            l=30,
            r=30,
            t=60,
            b=90,
        ),
    )

    st.plotly_chart(
        completion_fig,
        use_container_width=True,
        config=_chart_config(),
    )


def main() -> None:
    """Main dashboard page."""
    st.set_page_config(
        page_title="Dashboard",
        layout="wide",
    )

    init_session_state()

    render_sidebar(
        "Dashboard"
    )

    render_page_header(
        "Dashboard",
        (
            "Executive analytics from personas, "
            "surveys, interviews, and extracted insights."
        ),
    )

    personas = require_personas()

    if personas is None:
        return

    if not personas:
        st.warning(
            "No personas are available. "
            "Generate personas from the Workspace first."
        )
        st.page_link(
            "pages/workspace.py",
            label="Open Workspace",
        )
        return

    filtered_personas = _filter_personas(
        personas
    )

    if not filtered_personas:
        st.warning(
            "No personas match the selected filters."
        )
        return

    experiment = get_experiment()
    survey_results = get_survey_results()
    interview_rows = get_interview_results()
    insights = get_insights()

    persona_df = persona_dataframe(
        filtered_personas
    )

    age_values = [
        value
        for value in persona_df["age"].dropna().tolist()
    ]

    average_age = (
        round(
            sum(age_values)
            / len(age_values),
            1,
        )
        if age_values
        else 0.0
    )

    product_fit = _safe_float(
        (
            insights or {}
        ).get(
            "product_fit_score"
        )
        or (
            survey_results or {}
        ).get(
            "product_fit_score",
            0,
        )
    )

    recommendation_score = _safe_float(
        (
            insights or {}
        ).get(
            "recommendation_score"
        )
        or (
            insights or {}
        ).get(
            "would_use_product_score",
            0,
        )
    )

    persona_quality = (
        round(
            float(
                persona_df[
                    "quality_score"
                ].mean()
            ),
            1,
        )
        if not persona_df.empty
        else 0.0
    )

    consultant = (
        st.session_state.get(
            "consultant_report"
        )
        or {}
    )

    _render_executive_summary(
        experiment,
        filtered_personas,
        survey_results,
        insights,
        average_age,
    )

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(
        4
    )

    metric_col1.metric(
        "Total Personas",
        len(filtered_personas),
    )

    metric_col2.metric(
        "Average Age",
        average_age,
    )

    metric_col3.metric(
        "Product Fit",
        (
            f"{product_fit:.1f} / 100"
            if survey_results or insights
            else "Pending"
        ),
    )

    metric_col4.metric(
        "Recommendation",
        (
            f"{recommendation_score:.1f} / 100"
            if insights
            else "Pending"
        ),
    )

    metric_col5, metric_col6, metric_col7, metric_col8 = st.columns(
        4
    )

    metric_col5.metric(
        "Persona Quality",
        f"{persona_quality:.1f} / 100",
    )

    metric_col6.metric(
        "Survey Responses",
        len(
            (
                survey_results or {}
            ).get(
                "responses",
                [],
            )
        ),
    )

    metric_col7.metric(
        "Interview Messages",
        len(interview_rows),
    )

    insight_confidence = _safe_float(
        (
            insights or {}
        ).get(
            "product_fit_confidence_score",
            0,
        )
    )

    metric_col8.metric(
        "Insight Confidence",
        (
            f"{insight_confidence:.0f}"
            if insights
            else "Pending"
        ),
    )

    with st.expander(
        "Experiment Overview",
        expanded=False,
    ):
        st.json(
            experiment
            or {
                "status": (
                    "No experiment metadata available."
                )
            }
        )

    if consultant:
        readiness_col1, readiness_col2 = st.columns(2)

        readiness_col1.metric(
            "Launch Readiness",
            f"{consultant.get('launch_readiness', 0)}%",
        )

        readiness_col2.metric(
            "Risk Score",
            f"{consultant.get('risk_score', 0)}/100",
        )

    (
        persona_tab,
        survey_tab,
        interview_tab,
        insight_tab,
        export_tab,
    ) = st.tabs(
        [
            "Persona Analytics",
            "Survey Analytics",
            "Interview Analytics",
            "Insight Analytics",
            "Export",
        ]
    )

    with persona_tab:
        _render_persona_analytics(
            filtered_personas,
            persona_df,
        )

    analytics: Dict[str, Any] | None = None

    with survey_tab:
        analytics = _render_survey_analytics(
            survey_results,
            filtered_personas,
            experiment,
            product_fit,
        )

    with interview_tab:
        _render_interview_analytics(
            interview_rows
        )

    with insight_tab:
        _render_insight_analytics(
            insights,
            filtered_personas,
            recommendation_score,
        )

    with export_tab:
        _render_export_tab(
            experiment,
            filtered_personas,
            survey_results,
            interview_rows,
            insights,
            analytics,
        )


if __name__ == "__main__":
    main()