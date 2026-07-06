# Synthetic User Generation Platform

## Project Overview

An AI-powered platform that generates realistic synthetic user personas based on product details using Google Gemini. The generated personas are enriched with realistic fake data using Faker, displayed as persona cards, and can be exported to a CSV file.

## Tech Stack

- Python
- Streamlit
- Google Gemini
- Faker
- Pandas
- LangChain
- LangGraph
- Supabase

## Project Structure

- `services/` - Backend services (Gemini integration, persona generation, Faker)
- `pages/` - Streamlit pages
- `data/` - CSV storage
- `models/` - Data models
- `config/` - Configuration files
- `database/` - Database configuration

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Team Modules

- Member 1: Streamlit UI
- Member 2: Gemini AI Integration
- Member 3: Persona Generator & Faker
- Member 4: Persona Cards & CSV Export
- Member 5: Project Lead / Integration