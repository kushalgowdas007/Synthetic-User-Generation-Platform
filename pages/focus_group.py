from __future__ import annotations

import json
import streamlit as st
from frontend.shared import (
    get_experiment,
    increment_state_version,
    init_session_state,
    render_page_header,
    render_sidebar,
    render_synthetic_disclaimer,
    require_personas,
)
from services.focus_group_service import run_focus_group


def main() -> None:
    st.set_page_config(page_title="Focus Group | AI Research Studio", layout="wide")
    init_session_state()
    render_sidebar("Focus Group")
    render_page_header(
        "AI Focus Group Simulation",
        "Moderate a realistic multi-persona discussion to capture converging feedback, objections, and group dynamics.",
        active_stage="Focus Group",
    )

    personas = require_personas()
    if personas is None:
        return

    question = st.text_area(
        "Moderator Question",
        placeholder="What would make you choose this product over your current approach, and what concerns do you have about pricing or onboarding?",
        height=90,
    )

    if st.button("🚀 Run Focus Group Discussion", use_container_width=True):
        if not question.strip():
            st.error("Please provide a moderator prompt or question.")
        else:
            with st.spinner("Simulating multi-persona group discussion..."):
                st.session_state["focus_group_results"] = run_focus_group(question, personas, get_experiment())
                st.session_state["insights"] = None
                st.session_state["consultant_report"] = None
                st.session_state["product_actions"] = []
                increment_state_version()
                st.session_state["toast_message"] = "Focus group discussion complete."
                st.rerun()

    turns = st.session_state.get("focus_group_results", [])
    if not turns:
        st.info("Submit a moderator question above to simulate a discussion across your synthetic panel.")
    else:
        st.subheader("Focus Group Discussion Transcript")
        for turn in turns:
            is_mod = turn.get("role") == "moderator"
            with st.chat_message("user" if is_mod else "assistant"):
                st.markdown(f"**{turn.get('speaker', 'Participant')}** _({turn.get('role', 'speaker')})_")
                st.write(turn.get("message", ""))

        st.divider()
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            st.download_button(
                "Download discussion JSON",
                json.dumps(turns, indent=2).encode("utf-8"),
                "focus_group.json",
                "application/json",
                use_container_width=True,
            )
        with export_col2:
            st.page_link("pages/insights.py", label="Open Insight Engine →", use_container_width=True)

    st.divider()
    render_synthetic_disclaimer()


if __name__ == "__main__":
    main()
