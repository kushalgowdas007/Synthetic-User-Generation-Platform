# QA Report

## Scope and execution

Tested the workspace, persona generation, persona cards, survey, memory, interview, insights, dashboard, PDF export, JSON-compatible export, and CSV export paths. UI checks used Streamlit's application-testing interface from the real `app.py` entry point and navigated through every child page.

## Results

- Automated suite: **13 passed, 1 skipped** in 6.37 seconds.
- Skipped test: the live Gemini integration test is intentionally opt-in and requires `RUN_LIVE_GEMINI_TESTS=1` plus valid credentials.
- Source compilation: passed.
- Offline Gemini fallback: passed with a 10-persona generation request.
- Invalid workspace submission: correctly displays validation error.
- Survey execution, custom/template survey coverage, session-backed memory, insights, dashboard rendering, PDF bytes, and CSV/JSON-compatible serialization: passed.

## Bugs found and fixed

1. **Broken test import for application memory consistency checker** - `backend.app.memory.consistency_checker` was missing. Added a minimal compatibility adapter to the canonical checker.
2. **Naive UTC timestamps** - memory models and conversation history used deprecated `datetime.utcnow()`. Replaced with timezone-aware UTC timestamps.
3. **QA page-navigation setup** - Streamlit child pages must be tested from the main application entry point so the page registry exists. Updated UI smoke tests to mirror user navigation.

## Remaining known issues

- The original `.venv` was created against a removed Python 3.11 installation and cannot launch. A working `.venv-qa` was created and used for this QA run. Recreate `.venv` from a supported local interpreter before developer handoff.
- Live Gemini API behavior was not exercised because it requires external credentials/network access. The Gemini-unavailable fallback was verified.
- The in-app browser runtime could not initialize in this managed environment due to a filesystem permission restriction. Streamlit UI tests covered the same page rendering and interaction paths.

## Final production readiness score

**96/100** - all local functionality and offline resilience checks pass. The remaining score is reserved for a credentialed live-Gemini test, visual browser session check, and replacement of the stale developer virtual environment.
