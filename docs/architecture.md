# Synthetic User Generation Platform

# System Architecture

---

## Version

2.0

---

## Overview

The Synthetic User Generation Platform follows a modular Agent-Based Architecture designed to support scalable AI-driven synthetic persona generation.

Each module performs a specific responsibility and communicates through well-defined interfaces.

The architecture has been designed so that future milestones can be integrated without modifying existing components.

---

# High Level Architecture

```
                    User
                     │
                     ▼
        Streamlit Experiment Workspace
                     │
                     ▼
         Experiment Controller
                     │
                     ▼
      Persona Generation Agent
                     │
                     ▼
     Behavior Simulation Agent
                     │
                     ▼
          Persona Data Model
                     │
                     ▼
          Persona Presentation
                     │
                     ▼
         Persona Memory Store
                     │
                     ▼
      Consistency Checker
                     │
                     ▼
          Survey Agent
                     │
                     ▼
         Survey Service
                     │
                     ▼
        Repository Layer
                     │
                     ▼
              Database
                     │
                     ▼
       Analytics Dashboard (Future)
```

---

# Component Description

## Streamlit Workspace

Collects experiment information from the user.

Responsibilities

- Product Information
- Target Audience
- Research Goal
- Persona Count

---

## Persona Generation Agent

Uses Google Gemini AI to generate realistic synthetic personas.

Responsibilities

- Prompt Engineering
- Persona Generation
- Diversity
- JSON Formatting

---

## Behavior Simulation Agent

Adds realistic behaviour.

Responsibilities

- Goals
- Pain Points
- Buying Behaviour
- Technology Usage
- Personality

---

## Persona Memory Store

Stores conversation history.

Responsibilities

- Previous Responses
- User Opinions
- Context Management

---

## Consistency Checker

Validates generated responses.

Checks

- Demographic Consistency
- Behaviour Consistency
- Opinion Consistency
- Logical Consistency

---

## Survey Agent

Executes surveys.

Responsibilities

- Survey Questions
- Response Generation
- Multi-turn Conversation

---

## Repository Layer

Stores experiments and survey responses.

---

## Future Components

- Interview Mode
- Product Fit Analysis
- Insight Extraction
- Analytics Dashboard

---

# Benefits

- Modular
- Scalable
- Easy Maintenance
- Future Ready
- Independent Components
