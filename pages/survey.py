from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from backend.services.survey_service import (
    SURVEY_TEMPLATES,
    create_survey,
    execute_survey,
)
from frontend.shared import (
    get_experiment,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)


def _parse_custom_questions(raw_text: str) -> list[dict]:
    """Convert one-question-per-line text into survey question objects."""
    questions: list[dict] = []

    for index, line in enumerate(raw_text.splitlines()):
        text = line.strip(" -\t")

        if not text:
            continue

        questions.append(
            {
                "id": f"custom_{index + 1}",
                "question": text,
                "category": "Custom",
                "type": "single_choice",
                "options": [
                    "Very unlikely",
                    "Unlikely",
                    "Likely",
                    "Very likely",
                ],
                "weight": 1,
            }
        )

    return questions


def main() -> None:
    st.set_page_config(
        page_title="Survey",
        page_icon="📝",
        layout="wide",
    )

    init_session_state()
    render_sidebar("Survey")

    render_page_header(
        "Survey",
        "Generate simulated survey responses from the personas already stored in session state.",
    )

    # --------------------------------------------------
    # Load Personas
    # --------------------------------------------------

    personas = require_personas()

    if personas is None:
        return

    experiment = get_experiment()

    default_product = str(
        experiment.get("product_name") or ""
    ).strip()

    default_goal = str(
        experiment.get("research_objective")
        or experiment.get("research_goal")
        or ""
    ).strip()

    st.success(
        f"{len(personas)} personas loaded from "
        "st.session_state['personas']."
    )

    # --------------------------------------------------
    # Survey Configuration
    # --------------------------------------------------

    with st.form("survey_form"):

        setup_col1, setup_col2 = st.columns(2)

        with setup_col1:

            template_name = st.selectbox(
                "Survey Template",
                list(SURVEY_TEMPLATES.keys()),
            )

            include_dynamic_questions = st.checkbox(
                "Include dynamic product-fit questions",
                value=True,
            )

        with setup_col2:

            custom_questions_text = st.text_area(
                "Custom Questions",
                placeholder=(
                    "What would make you trust this product?\n"
                    "What feature would you use first?"
                ),
                height=110,
            )

        product_name = st.text_input(
            "Product Name",
            value=default_product,
        )

        research_goal = st.text_area(
            "Research Objective",
            value=default_goal,
            height=120,
        )

        submitted = st.form_submit_button(
            "🚀 Run Survey",
            use_container_width=True,
        )

    # --------------------------------------------------
    # Build Survey Preview
    # --------------------------------------------------

    custom_questions = _parse_custom_questions(
        custom_questions_text
    )

    template_questions = list(
        SURVEY_TEMPLATES.get(
            template_name,
            [],
        )
    )

    preview_questions = (
        template_questions + custom_questions
    )

    try:
        preview_payload = create_survey(
            product_name=product_name,
            research_goal=research_goal,
            survey_questions=preview_questions,
            template_name=template_name,
            include_dynamic_questions=include_dynamic_questions,
        )
    except Exception:
        # Some versions of survey_service may expose
        # create_survey with a slightly different signature.
        preview_payload = preview_questions

    # --------------------------------------------------
    # Question Preview
    # --------------------------------------------------

    with st.expander(
        "📋 Survey Questions",
        expanded=False,
    ):

        if preview_payload:

            for question in preview_payload:

                question_id = question.get(
                    "id",
                    "question",
                )

                category = question.get(
                    "category",
                    "General",
                )

                question_text = question.get(
                    "question",
                    str(question),
                )

                st.write(
                    f"**{question_id} | {category}** - "
                    f"{question_text}"
                )

        else:
            st.info(
                "No survey questions are currently available."
            )

    # --------------------------------------------------
    # Run Survey
    # --------------------------------------------------

    if submitted:

        if not product_name.strip():

            st.error(
                "Please provide a Product Name."
            )
            return

        if not research_goal.strip():

            st.error(
                "Please provide a Research Objective."
            )
            return

        try:

            progress = st.progress(
                0,
                text="Preparing survey...",
            )

            with st.spinner(
                "Generating persona-consistent survey responses..."
            ):

                progress.progress(
                    20,
                    text="Loading personas...",
                )

                progress.progress(
                    40,
                    text="Building survey...",
                )

                survey_results = execute_survey(
                    personas,
                    product_name=product_name.strip(),
                    research_goal=research_goal.strip(),
                    survey_questions=preview_questions,
                    template_name=template_name,
                    include_dynamic_questions=(
                        include_dynamic_questions
                    ),
                )

                progress.progress(
                    80,
                    text="Calculating survey analytics...",
                )

            # Store results in shared session state.
            st.session_state[
                "survey_results"
            ] = survey_results

            # New survey should invalidate old insights.
            st.session_state[
                "insights"
            ] = None

            progress.progress(
                100,
                text="Survey completed",
            )

            st.success(
                "✅ Survey completed successfully."
            )

        except TypeError:
            # Compatibility fallback for an older
            # survey_service.execute_survey signature.
            try:

                with st.spinner(
                    "Running survey with compatible service mode..."
                ):

                    survey_results = execute_survey(
                        personas,
                        product_name=product_name.strip(),
                        research_goal=research_goal.strip(),
                    )

                st.session_state[
                    "survey_results"
                ] = survey_results

                st.session_state[
                    "insights"
                ] = None

                st.success(
                    "✅ Survey completed successfully."
                )

            except Exception as exc:

                st.error(
                    "Unable to run the survey. "
                    f"Detail: {exc}"
                )
                return

        except Exception as exc:

            st.error(
                "Unable to run the survey. "
                f"Detail: {exc}"
            )
            return

    # --------------------------------------------------
    # Load Survey Results
    # --------------------------------------------------

    survey_results = get_survey_results()

    if not survey_results:

        st.info(
            "Run the survey to generate responses "
            "and unlock the dashboard."
        )

        return

    # --------------------------------------------------
    # Extract Results
    # --------------------------------------------------

    responses = survey_results.get(
        "responses",
        [],
    )

    analytics = survey_results.get(
        "analytics",
        {},
    )

    # --------------------------------------------------
    # Summary Metrics
    # --------------------------------------------------

    metric_col1, metric_col2, metric_col3 = (
        st.columns(3)
    )

    metric_col1.metric(
        "Personas",
        len(personas),
    )

    metric_col2.metric(
        "Responses",
        len(responses),
    )

    metric_col3.metric(
        "Product Fit",
        f"{float(survey_results.get('product_fit_score', 0) or 0):.1f} / 100",
    )

    meta_col1, meta_col2, meta_col3 = (
        st.columns(3)
    )

    meta_col1.metric(
        "Template",
        survey_results.get(
            "template_name",
            "N/A",
        ),
    )

    meta_col2.metric(
        "Categories",
        len(
            survey_results.get(
                "question_categories",
                [],
            )
        ),
    )

    meta_col3.metric(
        "Avg Confidence",
        f"{float(analytics.get('average_confidence', 0) or 0):.1f}",
    )

    st.progress(
        1.0,
        text=(
            "Survey progress: all assigned "
            "persona responses completed"
        ),
    )

    # --------------------------------------------------
    # Response Data
    # --------------------------------------------------

    responses_df = pd.DataFrame(
        responses
    )

    if not responses_df.empty:

        st.subheader(
            "📊 Response Analytics"
        )

        chart_col1, chart_col2 = (
            st.columns(2)
        )

        # ----------------------------------------------
        # Category Scores
        # ----------------------------------------------

        with chart_col1:

            category_frame = pd.DataFrame(
                [
                    {
                        "Category": key,
                        "Average Score": value,
                    }
                    for key, value in analytics.get(
                        "average_by_category",
                        {},
                    ).items()
                ]
            )

            if not category_frame.empty:

                st.plotly_chart(
                    px.bar(
                        category_frame,
                        x="Category",
                        y="Average Score",
                        title=(
                            "Average Score by Category"
                        ),
                    ),
                    use_container_width=True,
                )

        # ----------------------------------------------
        # Sentiment
        # ----------------------------------------------

        with chart_col2:

            sentiment_frame = pd.DataFrame(
                [
                    {
                        "Sentiment": key.title(),
                        "Count": value,
                    }
                    for key, value in analytics.get(
                        "sentiment_distribution",
                        {},
                    ).items()
                ]
            )

            if not sentiment_frame.empty:

                st.plotly_chart(
                    px.pie(
                        sentiment_frame,
                        names="Sentiment",
                        values="Count",
                        title="Survey Sentiment",
                    ),
                    use_container_width=True,
                )

        # --------------------------------------------------
        # Adoption Barriers
        # --------------------------------------------------

        barrier_frame = pd.DataFrame(
            [
                {
                    "Barrier": key,
                    "Count": value,
                }
                for key, value in analytics.get(
                    "adoption_barriers",
                    {},
                ).items()
            ]
        )

        if not barrier_frame.empty:

            st.plotly_chart(
                px.bar(
                    barrier_frame,
                    x="Count",
                    y="Barrier",
                    orientation="h",
                    title=(
                        "Product Adoption Barriers"
                    ),
                ),
                use_container_width=True,
            )

        # --------------------------------------------------
        # Survey Responses Table
        # --------------------------------------------------

        st.subheader(
            "📝 Survey Responses"
        )

        st.dataframe(
            responses_df,
            use_container_width=True,
            hide_index=True,
        )

        # --------------------------------------------------
        # Export
        # --------------------------------------------------

        export_col1, export_col2 = (
            st.columns(2)
        )

        with export_col1:

            st.download_button(
                "⬇ Download Survey Results JSON",
                data=json.dumps(
                    survey_results,
                    indent=2,
                    default=str,
                ).encode("utf-8"),
                file_name="survey_results.json",
                mime="application/json",
                use_container_width=True,
            )

        with export_col2:

            st.download_button(
                "⬇ Download Survey Responses CSV",
                data=responses_df.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="survey_responses.csv",
                mime="text/csv",
                use_container_width=True,
            )

    else:

        st.warning(
            "Survey results were generated, "
            "but no response rows are available."
        )

    # --------------------------------------------------
    # Navigation
    # --------------------------------------------------

    st.divider()

    st.subheader(
        "Continue Research"
    )

    navigation_col1, navigation_col2, navigation_col3 = (
        st.columns(3)
    )

    with navigation_col1:

        st.page_link(
            "pages/interview.py",
            label="💬 Open Interview",
        )

    with navigation_col2:

        st.page_link(
            "pages/insights.py",
            label="🧠 Open Insights",
        )

    with navigation_col3:

        st.page_link(
            "pages/dashboard.py",
            label="📊 Open Dashboard",
        )


if __name__ == "__main__":
    main()