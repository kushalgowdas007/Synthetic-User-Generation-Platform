# Synthetic User Generation Platform

An end-to-end Streamlit application for generating synthetic user personas, running simulated survey responses, and presenting analytics for product research.

## Demo Flow

```text
Workspace
  -> Generate Personas
  -> Persona Cards
  -> Survey
  -> Interview
  -> Insights
  -> Dashboard
```

## Current Features

- Streamlit multipage application with `app.py` as the single entry point.
- Workspace page for experiment setup and persona generation.
- One canonical persona generator in `services/persona_generator.py`.
- Gemini generation through the current `google-genai` SDK with Faker-backed contact enrichment.
- Local Faker fallback when Gemini credentials or API access are unavailable.
- Shared `st.session_state["personas"]`, `st.session_state["experiment"]`, and `st.session_state["survey_results"]` across all pages.
- Explicit local workspace save/load and experiment history in `data/workspace_history.json`; saved workspaces also retain interview memory.
- Persona Cards page with search, filters, sorting, cards, CSV export, and JSON export.
- Survey page that consumes generated personas without regenerating them.
- Survey templates for adoption, pricing/value, and usability/trust, with optional custom questions.
- Interview mode with persona memory, opinions, and conversation history.
- Insight extraction for themes, sentiment, behavior patterns, recommendations, top quotes, product feedback, and segmentation.
- Insight confidence, keyword frequency, topic clusters, risk analysis, and executive summary.
- Dashboard page that reads experiment, personas, survey results, interview data, and insights for KPIs, charts, product-fit analytics, and report downloads.

## Project Structure

```text
Synthetic-User-Generation-Platform/
|-- app.py
|-- pages/
|   |-- persona_cards.py
|   |-- survey.py
|   |-- interview.py
|   |-- insights.py
|   `-- dashboard.py
|-- frontend/
|   |-- shared.py
|   |-- app.py
|   `-- pages/
|-- services/
|   |-- persona_generator.py
|   `-- faker_service.py
|-- backend/
|   |-- services/
|   `-- tests/
|-- models/
|-- config/
|-- data/
|-- docs/
`-- requirements.txt
```

## Installation

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
SUPABASE_URL=YOUR_SUPABASE_URL
SUPABASE_KEY=YOUR_SUPABASE_KEY
```

Only `GEMINI_API_KEY` is required for Gemini persona generation. If it is missing, the app still works with local Faker-backed demo personas.

## Running

```bash
streamlit run app.py
```

## Testing

```bash
python -m compileall app.py services pages frontend backend models
python -m pytest
```

For an optional live Gemini check, set `RUN_LIVE_GEMINI_TESTS=1` and provide `GEMINI_API_KEY`. Normal tests use local deterministic fallbacks and never require a network call.

## Deployment

Set `GEMINI_API_KEY` (and optionally `GEMINI_MODEL`) in the deployment secret manager, install `requirements.txt`, and run `streamlit run app.py`. Do not commit a populated `.env` file. The application remains fully usable without Gemini through its Faker-backed persona and local interview fallbacks.

## Presentation Notes

The project is demo-ready for the main internship workflow:

1. Enter experiment details in Workspace.
2. Generate personas once.
3. Open Persona Cards and inspect/export personas.
4. Open Survey and run simulated responses.
5. Open Interview and ask persona-specific questions.
6. Open Insights and extract research findings.
7. Open Dashboard and present analytics/report exports.
