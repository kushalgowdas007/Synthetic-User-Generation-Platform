from __future__ import annotations

import json
import streamlit as st
from frontend.shared import get_experiment, init_session_state, render_page_header, render_sidebar, require_personas
from services.focus_group_service import run_focus_group


def main() -> None:
    st.set_page_config(page_title="Focus Group | AI Research Studio", layout="wide")
    init_session_state(); render_sidebar("Focus Group")
    render_page_header("AI Focus Group", "Moderate a realistic multi-persona discussion and capture converging or conflicting opinions.")
    personas = require_personas()
    if personas is None: return
    question = st.text_area("Moderator question", placeholder="What would make you choose this product over your current approach?", height=90)
    if st.button("Run discussion", use_container_width=True):
        if not question.strip(): st.error("Add a moderator question.")
        else:
            st.session_state["focus_group_results"] = run_focus_group(question, personas, get_experiment())
            st.session_state["consultant_report"] = None
            st.session_state["toast_message"] = "Focus group discussion generated."
            st.rerun()
    turns = st.session_state.get("focus_group_results", [])
    if not turns: st.info("Ask one question to hear a diverse panel respond."); return
    for turn in turns:
        with st.chat_message("assistant" if turn.get("role") == "participant" else "user"):
            st.caption(turn.get("speaker", "")); st.write(turn.get("message", ""))
    st.download_button("Download discussion JSON", json.dumps(turns, indent=2).encode(), "focus_group.json", "application/json")
    st.page_link("pages/insights.py", label="Analyze in Insight Engine →")

if __name__ == "__main__": main()
