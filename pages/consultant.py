from __future__ import annotations

import json
import streamlit as st
from frontend.shared import get_experiment, get_insights, get_survey_results, init_session_state, render_page_header, render_sidebar
from services.consultant_service import build_consultant_report


def main() -> None:
    st.set_page_config(page_title="Product Consultant | AI Research Studio", layout="wide")
    init_session_state(); render_sidebar("Product Consultant")
    render_page_header("AI Product Consultant", "Convert research signals into an explainable launch recommendation and practical roadmap.")
    if st.button("Generate executive recommendation", use_container_width=True):
        st.session_state["consultant_report"] = build_consultant_report(get_experiment(), get_insights(), get_survey_results(), st.session_state.get("focus_group_results", []))
    report = st.session_state.get("consultant_report")
    if not report: st.info("Generate insights first for the strongest recommendation. This page also works with survey results alone."); return
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Launch readiness", f"{report['launch_readiness']}%")
    c2.metric("Market fit", f"{report['market_fit']}/100")
    c3.metric("Revenue potential", report["revenue_potential"])
    c4.metric("Risk score", f"{report['risk_score']}/100")
    st.info("Why this recommendation: " + report["why"])
    st.subheader("What to do next")
    for item in report["business_recommendations"]: st.write("• " + item)
    left,right = st.columns(2)
    with left:
        st.subheader("Feature priority"); [st.write("• " + item) for item in report["feature_priorities"]]
        st.subheader("Roadmap"); [st.write("• " + item) for item in report["roadmap"]]
    with right:
        st.subheader("SWOT")
        for key, values in report["swot"].items(): st.write(f"**{key.title()}**"); [st.write("• " + item) for item in values]
    st.download_button("Download consultant report JSON", json.dumps(report, indent=2).encode(), "consultant_report.json", "application/json")

if __name__ == "__main__": main()
