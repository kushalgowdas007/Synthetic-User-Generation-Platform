from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend.shared import (
    get_experiment,
    get_interview_results,
    init_session_state,
    records_to_dataframe,
    render_page_header,
    render_sidebar,
    require_personas,
)
from services.interview_service import create_memory_payload, flatten_interview_memories, generate_interview_reply


def _persona_label(persona: dict) -> str:
    return f"{persona.get('name', 'Persona')} - {persona.get('occupation', 'Not provided')}"


def main() -> None:
    st.set_page_config(page_title="Interview", layout="wide")
    init_session_state()
    render_sidebar("Interview")
    render_page_header("Interview Mode", "Conduct persona-consistent interviews with memory-backed synthetic users.")

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

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader(persona.get("name", "Persona"))
        st.write(f"**Occupation:** {persona.get('occupation', 'Not provided')}")
        st.write(f"**Technology Usage:** {persona.get('technology_usage', 'Not provided')}")
        st.write(f"**Buying Behavior:** {persona.get('buying_behavior', 'Not provided')}")
    with col2:
        st.subheader("Memory")
        st.json(memories[persona_id].get("opinions", {}))

    suggestion_cols = st.columns(3)
    suggestions = ["What would make you try this?", "What concerns you about pricing?", "What would make you trust it?"]
    for column, suggestion in zip(suggestion_cols, suggestions):
        with column:
            if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                st.session_state["interview_draft"] = suggestion

    for item in memories[persona_id].get("history", []):
        with st.chat_message("user" if item.get("role") == "user" else "assistant"):
            st.write(item.get("message", ""))

    question = st.chat_input("Ask this persona about needs, pricing, adoption, frustrations, or product fit")
    question = question or st.session_state.pop("interview_draft", None)
    if question:
        with st.spinner("Interviewing persona..."):
            result = generate_interview_reply(
                persona=persona,
                user_message=question,
                memory_payload=memories[persona_id],
                experiment=get_experiment(),
            )
        memories[persona_id] = result["memory"]
        st.session_state["persona_memories"] = memories
        st.session_state["interview_results"] = flatten_interview_memories(memories)
        st.session_state["insights"] = None
        st.rerun()

    rows = get_interview_results()
    if rows:
        st.subheader("Interview Transcript")
        frame = records_to_dataframe(rows)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button(
            "Download interview transcript CSV",
            data=frame.to_csv(index=False).encode("utf-8"),
            file_name="interview_transcript.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Ask a question to start the interview transcript.")


if __name__ == "__main__":
    main()
