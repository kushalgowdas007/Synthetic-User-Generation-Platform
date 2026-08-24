from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from frontend.shared import (
    get_experiment,
    get_interview_results,
    increment_state_version,
    init_session_state,
    records_to_dataframe,
    render_page_header,
    render_sidebar,
    render_synthetic_disclaimer,
    require_personas,
)
from services.interview_service import create_memory_payload, flatten_interview_memories, generate_interview_reply


def _persona_label(persona: dict) -> str:
    return f"{persona.get('name', 'Persona')} - {persona.get('occupation', 'Not provided')}"


def main() -> None:
    st.set_page_config(page_title="Interview", layout="wide")
    init_session_state()
    render_sidebar("Interview")
    render_page_header(
        "Interview Mode",
        "Conduct persona-consistent 1-on-1 qualitative interviews with memory-backed synthetic users.",
        active_stage="Interview",
    )

    personas = require_personas()
    if personas is None:
        return

    memories = st.session_state.setdefault("persona_memories", {})
    labels = [_persona_label(persona) for persona in personas]
    selected_label = st.selectbox("Select Persona", labels)
    selected_index = labels.index(selected_label)
    persona = personas[selected_index]
    persona_id = str(persona.get("id", persona.get("name", selected_index)))
    memories.setdefault(persona_id, create_memory_payload(persona))

    memory_payload = memories[persona_id]
    consistency_score = int(memory_payload.get("consistency_score", 100) or 100)
    contradictions = memory_payload.get("contradictions", [])
    warnings = memory_payload.get("warnings", [])

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(persona.get("name", "Persona"))
        st.write(f"**Occupation:** {persona.get('occupation', 'Not provided')}")
        st.write(f"**Technology Usage:** {persona.get('technology_usage', 'Not provided')}")
        st.write(f"**Buying Behavior:** {persona.get('buying_behavior', 'Not provided')}")
        st.write(f"**Core Goal:** {(persona.get('goals', ['N/A']) or ['N/A'])[0]}")
    with col2:
        st.subheader("Memory & Consistency Audit")

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Current Emotion", str(memory_payload.get("emotional_state", "neutral")).title())
        metric_col2.metric("Consistency Score", f"{consistency_score}/100")
        st.write("**Conversation Summary**")
        st.write(memory_payload.get("conversation_summary", "No interview responses have been captured yet."))

        if contradictions:
            with st.expander("⚠ Detected Contradictions", expanded=True):
                for c in contradictions:
                    ref = c.get("turn_reference", "Turn") if isinstance(c, dict) else "Turn"
                    desc = c.get("description", str(c)) if isinstance(c, dict) else str(c)
                    st.warning(f"**[{ref}]**: {desc}")

        with st.expander("Tracked Persona Opinions", expanded=False):

          memory_payload = memories[persona_id]
        
        # Phase 7: Interview Consistency Audit
        from services.persona_consistency import check_interview_consistency
        history_items = memory_payload.get("history", [])
        audit_report = check_interview_consistency(history_items, persona)

        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric("Emotion", str(memory_payload.get("emotional_state", "neutral")).title())
        metric_col2.metric("Consistency Audit", f"{audit_report.consistency_score}/100")
        
        if audit_report.warnings:
            for warn in audit_report.warnings:
                st.warning(warn)

        st.write("**Conversation Summary**")
        st.write(memory_payload.get("conversation_summary", "No interview responses have been captured yet."))
        
        with st.expander("🔍 Consistency Audit & Contradictions", expanded=False):
            if audit_report.contradictions:
                for c in audit_report.contradictions:
                    st.error(f"[{c.severity} Severity] {c.topic}: {c.contradiction}")
                    st.caption(f"User: {c.turn_user}")
                    st.caption(f"Persona: {c.turn_assistant}")
            else:
                st.success("No self-contradictions detected in conversation memory.")
                
        with st.expander("Tracked Opinions", expanded=False):

            st.json(memory_payload.get("opinions", {}))

    st.divider()
    st.subheader("Suggested Discussion Starters")
    suggestion_cols = st.columns(3)
    suggestions = ["What would make you try this?", "What concerns you about pricing?", "What would make you trust it?"]
    chosen_starter = None
    for column, suggestion in zip(suggestion_cols, suggestions):
        with column:
            if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                chosen_starter = suggestion

    # Render Conversation Messages
    history_items = memories[persona_id].get("history", [])
    if history_items:
        st.subheader("Conversation History")
        for item in history_items:
            with st.chat_message("user" if item.get("role") == "user" else "assistant"):
                st.write(item.get("message", ""))
                if item.get("role") in ("persona", "assistant") and item.get("emotional_state"):
                    st.caption(f"Tone: {item.get('emotional_state')} | Topic: {item.get('topic', 'general')}")

    st.subheader("Suggested Follow-up Questions")
    follow_up_question = None
    follow_up_columns = st.columns(3)
    for index, follow_up in enumerate(memories[persona_id].get("follow_up_questions", [])[:3]):
        with follow_up_columns[index % 3]:
            if st.button(follow_up, key=f"followup_{persona_id}_{index}", use_container_width=True):
                follow_up_question = str(follow_up)

    user_input = st.chat_input("Ask this persona about needs, pricing, adoption, frustrations, or product fit")


    # Resolve active question
    active_question = user_input or follow_up_question or chosen_starter
    if active_question:
        with st.spinner(f"Interviewing {persona.get('name', 'persona')}..."):

         active_question = question or follow_up_question or st.session_state.pop("interview_draft", None)
    if active_question:
        with st.spinner("Interviewing persona..."):
            result = generate_interview_reply(
                persona=persona,
                user_message=active_question,
                memory_payload=memories[persona_id],
                experiment=get_experiment(),
            )
        memories[persona_id] = result["memory"]
        st.session_state["persona_memories"] = memories
        st.session_state["interview_results"] = flatten_interview_memories(memories)
        st.session_state["insights"] = None
        st.session_state["consultant_report"] = None
        st.session_state["product_actions"] = []
        increment_state_version()
        st.rerun()

    rows = get_interview_results()
    if rows:
        st.divider()
        st.subheader("Cohort Interview Transcript")
        frame = records_to_dataframe(rows)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            st.download_button(
                "Download interview transcript CSV",
                data=frame.to_csv(index=False).encode("utf-8"),
                file_name="interview_transcript.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with export_col2:
            st.download_button(
                "Download interview memory JSON",
                data=json.dumps(memories, indent=2).encode("utf-8"),
                file_name="interview_memory.json",
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.info("Ask a question above or click a suggestion to begin the interview.")

    st.divider()
    render_synthetic_disclaimer()


if __name__ == "__main__":
    main()
