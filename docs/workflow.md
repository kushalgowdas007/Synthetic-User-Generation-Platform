# Synthetic User Generation Platform

# Experiment Workflow

---

## Version

1.0

---

## Prepared By

Member 5 – Technical Lead

---

# 1. Overview

The Experiment Workflow defines how data flows through the Synthetic User Generation Platform from user input to persona generation, behavioural modelling, and future survey execution.

The workflow is designed to be modular so that new AI agents can be integrated without modifying the existing architecture.

---

# 2. Current Workflow (Milestone 1)

The current implementation follows these steps:

1. User opens the Streamlit application.
2. User enters experiment details.
3. Workspace validates the input.
4. Persona Generation Agent sends the prompt to Google Gemini.
5. Gemini generates synthetic personas.
6. Behaviour Simulation enriches each persona.
7. Persona Cards are displayed.
8. Persona data is stored.

---

# 3. Future Workflow (Milestone 2)

The future workflow extends persona generation with persistent memory and survey execution.

Additional steps include:

1. Load Persona Memory.
2. Execute Survey.
3. Generate persona responses.
4. Validate consistency.
5. Update memory.

---

# 4. Future Workflow (Milestone 3)

Milestone 3 introduces analytics and insight generation.

Additional steps include:

1. Analyse survey responses.
2. Detect behavioural trends.
3. Calculate Product Fit Score.
4. Generate insights.
5. Display analytics dashboard.

---

# 5. Complete Workflow

```
User

↓

Streamlit Workspace

↓

Workspace Agent

↓

Persona Generation Agent

↓

Google Gemini

↓

Behaviour Simulation

↓

Persona Model

↓

Persona Cards

↓

CSV / Database Storage

-----------------------------

Milestone 2

↓

Memory Store

↓

Survey Agent

↓

Consistency Validation

-----------------------------

Milestone 3

↓

Insight Extraction

↓

Analytics Dashboard
```

---

# 6. Workflow Benefits

- Modular Architecture
- Independent AI Agents
- Scalable Design
- Easy Integration
- Supports Multi-turn Conversations
- Future Ready

---

# 7. Conclusion

The workflow provides a structured pipeline for persona generation while ensuring compatibility with future modules such as Memory, Survey Mode, Consistency Validation, and Analytics.