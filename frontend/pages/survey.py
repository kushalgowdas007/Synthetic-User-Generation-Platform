from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from backend.services.survey_service import execute_survey, generate_demo_dataset

st.set_page_config(page_title="Survey Mode", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .hero-card {
        border: 1px solid #dbeafe;
        border-radius: 20px;
        background: linear-gradient(135deg, #ffffff, #f8fafc);
        padding: 1.2rem 1.35rem;
        box-shadow: 0 14px 35px rgba(15, 23, 42, 0.07);
        margin-bottom: 1rem;
    }
    .hero-title {
        margin: 0;
        color: #0f172a;
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .hero-subtitle {
        margin: 0.35rem 0 0;
        color: #475569;
        font-size: 0.97rem;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        padding: 0.35rem 0.8rem;
        font-size: 0.78rem;
        font-weight: 700;
        margin-top: 0.7rem;
    }
    .form-shell {
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        background: #ffffff;
        padding: 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
        margin-bottom: 1rem;
    }
    .summary-shell {
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        background: #ffffff;
        padding: 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    }
    .stProgress > div > div > div { background: linear-gradient(90deg, #2563eb, #7c3aed); }
    .stButton > button {
        border-radius: 14px;
        height: 3rem;
        font-weight: 700;
        box-shadow: 0 8px 22px rgba(37, 99, 235, 0.15);
    }
    .question-card {
        border-left: 4px solid #2563eb;
        background: #f8fafc;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <h1 class="hero-title">📝 Survey Studio</h1>
        <p class="hero-subtitle">Run a polished research survey, simulate realistic responses, and prepare high-quality analytics output.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Research Controls")
    st.info("Use the controls below to execute or demo the survey workflow.")

with st.form("survey_form"):
    st.markdown("<div class='form-shell'>", unsafe_allow_html=True)
    product_name = st.text_input("Product name", value="FitPulse AI")
    research_goal = st.text_area(
        "Research goal",
        value="Understand adoption barriers and willingness to try the product.",
        height=120,
    )

    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("Run survey", use_container_width=True)
    with col2:
        demo_button = st.form_submit_button("Generate Demo Dataset", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

persona_source = st.session_state.get("personas")
if persona_source is None:
    persona_source = st.session_state.get("persona_cards")
if persona_source is None:
    persona_source = st.session_state.get("persona")

if not persona_source:
    st.warning("No personas are currently available in session state. Generate or load personas before running a survey.")
else:
    personas_count = len(persona_source) if isinstance(persona_source, list) else 1
    st.markdown(f'<div class="status-chip">📌 {personas_count} persona(s) available for analysis</div>', unsafe_allow_html=True)

if submitted:
    if not product_name.strip() or not research_goal.strip():
        st.error("Please provide both the product name and the research objective.")
    else:
        progress = st.progress(0, text="Loading Personas")
        progress.progress(18, text="Loading Personas")
        try:
            with st.spinner("Running survey and calculating product fit..."):
                survey_result = execute_survey(persona_source, product_name=product_name, research_goal=research_goal)
            progress.progress(64, text="Calculating Product Fit")
            progress.progress(100, text="Building Dashboard")
            st.session_state["survey_results"] = survey_result
            st.success("Survey completed successfully.")
            st.metric("Product Fit Score", f"{survey_result['product_fit_score']} / 100")

            responses_df = pd.DataFrame(survey_result["responses"])
            if not responses_df.empty:
                st.markdown("<div class='summary-shell'>", unsafe_allow_html=True)
                st.subheader("Response Highlights")
                response_cards = []
                for response in responses_df.head(6).to_dict("records"):
                    response_cards.append(
                        f"<div class='question-card'><strong>{response.get('question_id', 'Question')}</strong><br>{response.get('answer', 'No answer captured')}</div>"
                    )
                st.markdown("".join(response_cards), unsafe_allow_html=True)
                st.dataframe(responses_df, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as exc:
            st.error(f"Unable to execute the survey right now. Please review your persona data and try again. Detail: {exc}")

if demo_button:
    try:
        progress = st.progress(0, text="Generating Demo Dataset")
        progress.progress(24, text="Loading Personas")
        progress.progress(56, text="Simulating Survey Responses")
        with st.spinner("Generating demo dataset..."):
            demo_payload = generate_demo_dataset(product_name=product_name, research_goal=research_goal)
        progress.progress(100, text="Generating Report")
        st.session_state["personas"] = demo_payload["personas"]
        st.session_state["survey_results"] = demo_payload["survey_results"]
        st.session_state["research_report"] = demo_payload["research_report"]
        st.success("Demo dataset generated successfully.")
        st.info("The dashboard is now ready to demonstrate the full survey analytics workflow without relying on Gemini.")
    except Exception as exc:
        st.error(f"Unable to generate the demo dataset. Detail: {exc}")

if "survey_results" in st.session_state:
    survey_result = st.session_state["survey_results"]
    st.markdown("---")
    st.subheader("Survey Summary")
    st.metric("Overall product fit", f"{survey_result['product_fit_score']} / 100")
    responses_df = pd.DataFrame(survey_result["responses"])
    if not responses_df.empty:
        st.markdown("<div class='summary-shell'>", unsafe_allow_html=True)
        st.dataframe(responses_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            label="Export survey results as JSON",
            data=json.dumps(survey_result, indent=2).encode("utf-8"),
            file_name="survey_results.json",
            mime="application/json",
            use_container_width=True,
        )
