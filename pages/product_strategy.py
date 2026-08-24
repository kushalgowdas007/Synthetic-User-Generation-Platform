from __future__ import annotations

import json
import streamlit as st
from frontend.shared import (
    get_experiment,
    get_insights,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)
from services.consultant_service import build_consultant_report


def main() -> None:
    st.set_page_config(page_title="Product Strategy", page_icon="🎯", layout="wide")
    init_session_state()
    render_sidebar("Product Strategy")
    render_page_header("Product Strategy", "Translate research findings into launch roadmap, competitive positioning, and strategic priorities.")

    personas = require_personas()
    if personas is None:
        return

    experiment = get_experiment()
    insights = get_insights()
    survey_results = get_survey_results()

    if st.button("Build Product Strategy Report", use_container_width=True) or not st.session_state.get("consultant_report"):
        st.session_state["consultant_report"] = build_consultant_report(
            experiment, insights, survey_results, st.session_state.get("focus_group_results", [])
        )

    report = st.session_state.get("consultant_report", {})
    l_rec = report.get("launch_recommendation", {})

    if l_rec:
        st.subheader(f"Executive Decision: {l_rec.get('status', '🟢 Proceed with Validation')}")
        st.info(f"**Rationale:** {l_rec.get('rationale')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Launch Readiness", f"{report.get('launch_readiness', 0)}%")
    c2.metric("Market Fit Score", f"{report.get('market_fit', 0)}/100")
    c3.metric("Revenue Potential", str(report.get('revenue_potential', 'N/A')))
    c4.metric("Risk Level", f"{report.get('risk_score', 0)}/100")

    st.caption("**Strategic Rationale:** " + str(report.get("why", "N/A")))

    left, right = st.columns(2)
    with left:
        st.subheader("Feature Priorities")
        for feat in report.get("feature_priorities", []):
            st.write(f"• {feat}")

        st.subheader("Product Roadmap")
        for phase in report.get("roadmap", []):
            st.write(f"• {phase}")

    with right:
        st.subheader("SWOT Analysis")
        swot = report.get("swot", {})
        for k, vals in swot.items():
            st.write(f"**{k.title()}**")
            for v in vals:
                st.write(f"  - {v}")

    st.download_button(
        "Download Product Strategy JSON",
        data=json.dumps(report, indent=2).encode("utf-8"),
        file_name="product_strategy_report.json",
        mime="application/json",
        use_container_width=True
    )


if __name__ == "__main__":
    main()
