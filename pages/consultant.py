from __future__ import annotations

import json
import streamlit as st
from frontend.shared import (
    get_experiment,
    get_insights,
    get_personas,
    get_survey_results,
    increment_state_version,
    init_session_state,
    render_page_header,
    render_sidebar,
    render_synthetic_disclaimer,
    require_personas,
)
from services.consultant_service import build_consultant_report


def render_decision_card(decision: dict, rank: int) -> None:
    title = decision.get("title", "Strategic Decision")
    problem = decision.get("problem", "")
    recommendation = decision.get("recommendation", "")
    priority = decision.get("priority", 80)
    impact = decision.get("impact", 80)
    effort = decision.get("effort", 40)
    confidence = decision.get("confidence", 80)
    evidence_str = decision.get("evidence_strength", 80)
    urgency = decision.get("urgency", 75)
    affected = decision.get("affected_personas", [])
    outcomes = decision.get("expected_outcomes", [])
    sources = decision.get("source_insights", [])
    breakdown = decision.get("breakdown", {})

    with st.container(border=True):
        head_col1, head_col2 = st.columns([3, 1])
        with head_col1:
            st.markdown(f"### #{rank}: {title}")
        with head_col2:
            st.markdown(
                f'<div style="text-align:right;"><span style="background:linear-gradient(135deg,#6366f1,#a855f7);color:white;padding:6px 14px;border-radius:10px;font-size:1.1rem;font-weight:bold;">Priority: {priority}/100</span></div>',
                unsafe_allow_html=True,
            )

        # Transparent priority score breakdown
        st.markdown(
            f"**Transparent Priority Formula Breakdown:** "
            f"`Impact: {impact}` | `Confidence: {confidence}` | `Evidence: {evidence_str}` | `Urgency: {urgency}` | `Effort: {effort}`"
        )
        if breakdown and isinstance(breakdown, dict):
            st.caption(f"📐 Formula: {breakdown.get('formula_explanation', '')}")

        st.divider()

        q1, q2 = st.columns(2)
        with q1:
            st.markdown("**WHAT SHOULD WE DO?**")
            st.write(recommendation)
            st.markdown("**WHY? (Problem Signal)**")
            st.write(problem)
        with q2:
            st.markdown("**WHO IS AFFECTED?**")
            st.write(", ".join(affected) if affected else "All cohort personas")
            st.markdown("**EXPECTED OUTCOME**")
            for out in outcomes:
                st.write(f"• {out}")

        if sources:
            st.caption(f"Root Insights: {', '.join(sources)}")


def main() -> None:
    st.set_page_config(page_title="Product Strategy | AI Research Studio", layout="wide")
    init_session_state()
    render_sidebar("Product Consultant")
    render_page_header(
        "Action Center & Executive Product Strategy",
        "Translate research signals into an auditable launch roadmap and prioritized 'What Should We Do Next?' product decisions.",
        active_stage="Product Consultant",
    )

    personas = require_personas()
    if personas is None:
        return

    insights = get_insights()
    survey = get_survey_results()
    focus_group = st.session_state.get("focus_group_results", [])

    if st.button("🚀 Generate Executive Strategy & Prioritized Actions", use_container_width=True):
        with st.spinner("Synthesizing multi-source signals into prioritized product decisions..."):
            report = build_consultant_report(
                get_experiment(),
                insights,
                survey,
                focus_group,
                personas=personas,
            )
            st.session_state["consultant_report"] = report
            st.session_state["product_actions"] = report.get("decisions", [])
            increment_state_version()
        st.success("Executive strategy generated successfully.")

    report = st.session_state.get("consultant_report")
    if not report:
        st.info("Click 'Generate Executive Strategy & Prioritized Actions' to calculate launch readiness and top decisions.")
        return

    # Top Launch Readiness KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Launch Readiness", f"{report.get('launch_readiness', 0)}%")
    c2.metric("Market Fit Score", f"{report.get('market_fit', 0)}/100")
    c3.metric("Revenue Potential", str(report.get("revenue_potential", "Promising")))
    c4.metric("Risk Score", f"{report.get('risk_score', 0)}/100")

    st.info(f"💡 **Executive Rationale:** {report.get('why', '')}")

    # Central Experience: WHAT SHOULD WE DO NEXT?
    st.header("🎯 WHAT SHOULD WE DO NEXT?")
    st.caption("Top prioritized, evidence-backed product decisions ranked by impact, confidence, evidence strength, urgency, and effort.")

    top_decisions = report.get("top_decisions", [])
    if top_decisions:
        for idx, decision in enumerate(top_decisions, 1):
            render_decision_card(decision, idx)
    else:
        st.info("No prioritized decisions generated yet.")

    st.divider()

    # Strategic Roadmap & SWOT Analysis
    left, right = st.columns(2)
    with left:
        st.subheader("Implementation Roadmap")
        for item in report.get("roadmap", []):
            st.markdown(f"• **{item}**")

        st.subheader("High-Value Feature Priorities")
        for item in report.get("feature_priorities", []):
            st.markdown(f"• {item}")

    with right:
        st.subheader("SWOT Strategic Analysis")
        swot = report.get("swot", {})
        for key in ["strengths", "weaknesses", "opportunities", "threats"]:
            vals = swot.get(key, [])
            st.markdown(f"**{key.title()}:**")
            for v in vals:
                st.markdown(f"- {v}")

    st.divider()
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.download_button(
            "Download Executive Report JSON",
            json.dumps(report, indent=2).encode("utf-8"),
            "consultant_strategy_report.json",
            "application/json",
            use_container_width=True,
        )
    with exp_col2:
        st.page_link("pages/dashboard.py", label="Open Executive Analytics Dashboard →", use_container_width=True)

    st.divider()
    render_synthetic_disclaimer()


if __name__ == "__main__":
    main()
