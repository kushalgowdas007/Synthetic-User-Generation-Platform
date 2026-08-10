# Architecture Report

`app.py` and `pages/` form the Streamlit presentation layer. `frontend/shared.py` owns the session-state contract. `services/` contains canonical persona generation, interview, insight, report, and workspace persistence services. `backend/services/survey_service.py` is the survey analytics domain service. `models/persona.py` provides tolerant persona schema normalization.

Gemini is accessed only through the current `google-genai` SDK in the persona and interview services. Both paths retain local fallbacks so demonstrations remain operational without credentials.
## AI Research Studio Extension

The architecture remains Streamlit multipage plus shared `st.session_state` and service-layer functions. New pages call small deterministic services and write results to the existing session-first data model. `workspace_store` now serializes research plans, focus-group discussions, and consultant reports with the established experiment data.

This preserves the single canonical persona generator, survey engine, interview memory, insight engine, and report service while allowing each new feature to compose their output rather than duplicate generation logic.
