from __future__ import annotations

import json
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
from services.cache_service import compute_report_signature
from services.report_service import export_full_research_report_pdf


def main() -> None:
    st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")
    init_session_state()
    render_sidebar("Reports")
    render_page_header("Executive Reports", "Export publication-ready research reports in PDF, JSON, and CSV formats.")

    personas = require_personas()
    if personas is None:
        return

    experiment = get_experiment()
    survey_results = get_survey_results()
    interview_rows = get_interview_results()
    insights = get_insights()

    report_sig = compute_report_signature(experiment, personas, survey_results, insights)
    st.caption(f"Report Signature (SHA-256): `{report_sig[:16]}...`")

    st.subheader("Available Export Formats")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Full Research Report (PDF)")
        st.write("Contains executive summary, persona cards, survey analytics, interview highlights, and strategic recommendations.")
        if st.button("Generate PDF Report", use_container_width=True):
            with st.spinner("Generating ReportLab PDF document..."):
                pdf_bytes = export_full_research_report_pdf(
                    experiment=experiment,
                    personas=personas,
                    survey_results=survey_results,
                    interview_rows=interview_rows,
                    insights=insights,
                )
                st.session_state["generated_pdf"] = pdf_bytes
                st.success("PDF generated successfully!")

        if "generated_pdf" in st.session_state and st.session_state["generated_pdf"]:
            st.download_button(
                "⬇ Download PDF Report",
                data=st.session_state["generated_pdf"],
                file_name="ai_research_study_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    with col2:
        st.subheader("💾 Full Session Data (JSON)")
        st.write("Export complete raw data payload including personas, survey responses, interview transcripts, and insights.")

        full_payload = {
            "report_signature": report_sig,
            "experiment": experiment,
            "personas": personas,
            "survey_results": survey_results,
            "interview_results": interview_rows,
            "insights": insights,
            "product_actions": st.session_state.get("product_actions", []),
        }

        st.download_button(
            "⬇ Download Complete Research JSON",
            data=json.dumps(full_payload, indent=2, default=str).encode("utf-8"),
            file_name="complete_research_study.json",
            mime="application/json",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
