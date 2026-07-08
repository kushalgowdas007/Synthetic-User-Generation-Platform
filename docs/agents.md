# Synthetic User Generation Platform

# Agent Design Document

---

## Version

1.0

---

## Prepared By

Member 5 – Technical Lead

---

# 1. Introduction

The Synthetic User Generation Platform follows an Agent-Based AI Architecture.

Each agent is responsible for one specific task.

This architecture makes the platform:

- Modular
- Scalable
- Maintainable
- Easy to extend

Future milestones such as Persona Memory, Survey Mode, Consistency Validation, Interview Mode and Analytics can be added without redesigning the entire system.

---

# 2. Current Agents

The current implementation of the Synthetic User Generation Platform consists of four primary agents. Each agent performs a specific responsibility and communicates with the next agent in the workflow.

The modular design ensures that each component can be developed, tested, and maintained independently.

## 2.1 Workspace Agent

### Purpose

The Workspace Agent acts as the entry point of the application. It collects experiment details from the user through the Streamlit interface and prepares the request for persona generation.

### Responsibilities

- Collect Product Name
- Collect Product Description
- Collect Target Audience
- Collect Research Objective
- Validate user inputs
- Create the experiment request

### Input

| Field | Description |
|-------|-------------|
| Product Name | Name of the product |
| Product Description | Description of the product |
| Target Audience | Intended users |
| Research Objective | Goal of the experiment |

### Output

A validated experiment request that is forwarded to the Persona Generation Agent.

## 2.2 Persona Generation Agent

### Purpose

The Persona Generation Agent is responsible for creating realistic synthetic personas using Google Gemini AI.

### Responsibilities

- Generate diverse personas
- Use Google Gemini API
- Produce structured persona information
- Ensure variation among personas

### Input

Validated Experiment Request

### Output

One or more synthetic persona objects.

### Technologies Used

- Google Gemini API
- Prompt Engineering
- Python

## 2.3 Behavior Simulation Agent

### Purpose

The Behavior Simulation Agent enriches each generated persona by creating realistic behavioural characteristics.

### Responsibilities

- Generate personality traits
- Generate behaviour patterns
- Generate goals
- Generate pain points
- Generate technology usage
- Generate buying behaviour
- Generate lifestyle information

### Input

Generated Persona

### Output

Enhanced Persona with behavioural information.

## 2.4 Persona Presentation Agent

### Purpose

The Persona Presentation Agent is responsible for displaying generated personas in an easy-to-read visual format.

### Responsibilities

- Convert persona data into visual cards
- Improve readability
- Display generated personas using Streamlit
- Present information in a structured layout

### Output

Visual Persona Cards displayed on the user interface.

---

# 3. Future Agents (Milestone 2)

Milestone 2 extends the platform by introducing persistent persona memory, survey execution, and response consistency validation. These agents enable realistic multi-turn conversations and improve the quality of generated responses.

## 3.1 Persona Memory Agent

### Purpose

The Persona Memory Agent stores conversation history and previously expressed opinions for each persona. This allows personas to respond consistently across multiple interactions.

### Responsibilities

- Store conversation history
- Maintain persona opinions
- Retrieve previous responses
- Provide contextual memory to the LLM
- Support multi-turn conversations

### Input

- Persona ID
- Conversation History
- Previous Responses

### Output

Updated Memory Context

---

## 3.2 Survey Agent

### Purpose

The Survey Agent manages surveys by presenting questions to personas and collecting responses.

### Responsibilities

- Create surveys
- Execute surveys
- Generate responses
- Manage survey lifecycle
- Store responses

### Input

- Survey Details
- Persona Information

### Output

Survey Responses

---

## 3.3 Consistency Validation Agent

### Purpose

The Consistency Validation Agent verifies whether persona responses remain consistent throughout the conversation.

### Responsibilities

- Validate demographic consistency
- Validate behavioural consistency
- Detect contradictory opinions
- Calculate consistency score
- Generate validation reports

### Input

Persona Responses

### Output

Consistency Score

---

# 4. Future Agents (Milestone 3)

Milestone 3 focuses on extracting valuable insights from persona responses and providing advanced analytics to researchers.

## 4.1 Insight Extraction Agent

### Purpose

The Insight Extraction Agent analyses persona responses to identify common patterns, trends, and product insights.

### Responsibilities

- Analyse survey responses
- Identify common themes
- Extract user insights
- Generate summaries
- Detect behavioural trends

### Output

Research Insights

---

## 4.2 Analytics Agent

### Purpose

The Analytics Agent generates visual reports and performance metrics from collected persona data.

### Responsibilities

- Generate Product Fit Score
- Display Persona Statistics
- Survey Analytics
- Behaviour Reports
- Interactive Dashboards

### Output

Analytics Dashboard

---

# 5. Agent Communication Flow

The following diagram represents how the agents interact during persona generation and future survey execution.

```
User
   │
   ▼
Workspace Agent
   │
   ▼
Persona Generation Agent
   │
   ▼
Behavior Simulation Agent
   │
   ▼
Persona Presentation Agent
   │
   ▼
──────────────────────────────────
Future Workflow
   │
   ▼
Persona Memory Agent
   │
   ▼
Survey Agent
   │
   ▼
Consistency Validation Agent
   │
   ▼
Insight Extraction Agent
   │
   ▼
Analytics Agent
```

---

# 6. Benefits of the Agent-Based Architecture

The proposed architecture provides the following benefits:

- Modular software design
- Independent development of agents
- Easy integration of future modules
- Scalable AI architecture
- Simplified testing and debugging
- Better maintainability
- Support for multi-agent workflows
- Reusable software components

---

# 7. Conclusion

The Synthetic User Generation Platform adopts a modular Agent-Based Architecture to ensure flexibility, scalability, and maintainability. The current implementation supports persona generation, while the planned architecture seamlessly accommodates advanced features such as Persona Memory, Survey Mode, Consistency Validation, Insight Extraction, and Analytics without requiring major architectural changes.