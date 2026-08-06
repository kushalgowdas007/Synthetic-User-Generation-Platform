# Architecture Report

`app.py` and `pages/` form the Streamlit presentation layer. `frontend/shared.py` owns the session-state contract. `services/` contains canonical persona generation, interview, insight, report, and workspace persistence services. `backend/services/survey_service.py` is the survey analytics domain service. `models/persona.py` provides tolerant persona schema normalization.

Gemini is accessed only through the current `google-genai` SDK in the persona and interview services. Both paths retain local fallbacks so demonstrations remain operational without credentials.
