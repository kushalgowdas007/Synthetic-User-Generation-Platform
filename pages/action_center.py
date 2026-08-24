from __future__ import annotations

import json
import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.shared import (
    get_experiment,
    get_insights,
    init_session_state,
    render_page_header,
    render_sidebar,
    require_personas,
)
from services.decision_engine import generate_product_actions


def main() -> None:
    st.set_page_config(page_title="Action Center", page_icon="⚡", layout="wide")
    init_session_state()
    render_sidebar("Action Center")
    render_page_header("Action Center", "Convert high-value research insights into prioritized product decisions and actionable recommendations.")

    personas = require_personas()
    if personas is None:
        return

    experiment = get_experiment()
    insights = get_insights()

    # Generate or retrieve actions
    if "product_actions" not in st.session_state or st.session_state["product_actions"] is None or st.button("🔄 Refresh Product Decisions"):
        st.session_state["product_actions"] = generate_product_actions(insights, personas, experiment)

    actions = st.session_state.get("product_actions", [])

    if not actions:
        st.info("No product decisions generated yet. Extract insights to build recommendations.")
        return

    st.subheader("Top Product Decisions (\"WHAT SHOULD WE DO NEXT?\")")

    # Priority Summary Cards
    top_3 = actions[:3]
    for idx, act in enumerate(top_3, 1):
        with st.expander(f"#{idx} | {act.get('title')} (Priority {act.get('priority')}/100)", expanded=(idx == 1)):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**Problem:** {act.get('problem')}")
                st.markdown(f"**Recommendation:** {act.get('recommendation')}")
                st.markdown(f"**Source Insights:** {', '.join(act.get('source_insights', []))}")
            with col2:
                st.metric("Impact Score", f"{act.get('impact')}/100")
                st.metric("Confidence", f"{act.get('confidence')}/100")
                st.metric("Evidence Strength", f"{act.get('evidence_strength')}/100")
            with col3:
                st.metric("Affected Users", f"{act.get('affected_users_score')}/100")
                st.metric("Urgency", f"{act.get('urgency')}/100")
                st.metric("Effort Score", f"{act.get('effort')}/100")

            st.divider()
            st.write("**Transparent Priority Formula Breakdown:**")
            bd = act.get("priority_breakdown", {})
            st.caption(
                f"Priority ({act.get('priority')}) = 25% Impact ({bd.get('Impact')}) + 25% Confidence ({bd.get('Confidence')}) + "
                f"20% Evidence ({bd.get('Evidence Strength')}) + 15% Affected ({bd.get('Affected Users')}) + 15% (100 - Effort [{bd.get('Effort')}])"
            )

    st.divider()
    st.subheader("📋 Decision Board")
    
    # Categorize into 4 columns
    now_items = [a for a in actions if a.get("impact", 0) >= 70 and a.get("effort", 50) <= 45]
    next_items = [a for a in actions if a.get("impact", 0) >= 70 and a.get("effort", 50) > 45]
    later_items = [a for a in actions if a.get("impact", 0) < 70 and a.get("effort", 50) > 50]
    validate_items = [a for a in actions if a.get("evidence_strength", 80) < 60 or a not in (now_items + next_items + later_items)]

    board_col1, board_col2, board_col3, board_col4 = st.columns(4)
    
    with board_col1:
        st.write("🟢 **NOW** (High Impact / Low Effort)")
        for a in now_items or actions[:1]:
            st.info(f"**{a.get('title')}**\nPriority: {a.get('priority')}/100")
            
    with board_col2:
        st.write("🟡 **NEXT** (High Impact / Moderate Effort)")
        for a in next_items or actions[1:2]:
            st.warning(f"**{a.get('title')}**\nPriority: {a.get('priority')}/100")

    with board_col3:
        st.write("🔵 **LATER** (Strategic / High Effort)")
        for a in later_items or actions[2:3]:
            st.caption(f"**{a.get('title')}**\nPriority: {a.get('priority')}/100")

    with board_col4:
        st.write("🔍 **VALIDATE** (Needs Evidence)")
        for a in validate_items:
            st.write(f"• **{a.get('title')}** (Evidence: {a.get('evidence_strength')}%)")

    st.divider()
    st.subheader("Decision Matrix & Action Registry")

    frame = pd.DataFrame(actions)
    if not frame.empty:
        # Priority Scatter Chart
        fig = px.scatter(
            frame,
            x="effort",
            y="impact",
            size="priority",
            color="status",
            hover_name="title",
            text="title",
            title="Impact vs. Effort Decision Matrix",
            labels={"effort": "Effort (Lower is easier)", "impact": "Impact (Higher is better)"}
        )
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            frame[["title", "priority", "impact", "effort", "confidence", "evidence_strength", "status"]],
            use_container_width=True,
            hide_index=True
        )

    st.download_button(
        "Download Product Actions JSON",
        data=json.dumps(actions, indent=2).encode("utf-8"),
        file_name="product_actions.json",
        mime="application/json",
        use_container_width=True
    )


if __name__ == "__main__":
    main()
