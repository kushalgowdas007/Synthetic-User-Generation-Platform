from __future__ import annotations

import json
from typing import Any, Dict

import streamlit as st

from frontend.shared import (
    get_experiment,
    get_personas,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    save_personas,
)
from services.persona_generator import PersonaGenerator


def build_experiment_payload(
    *,
    experiment_name: str,
    product_name: str,
    description: str,
    target_audience: str,
    research_objective: str,
    industry: str,
    simulation_type: str,
    persona_count: int,
    age: str,
    gender: str,
    profession: str,
    location: str,
    interests: str,
) -> Dict[str, Any]:
    return {
        "experiment_name": experiment_name.strip(),
        "product_name": product_name.strip(),
        "description": description.strip(),
        "target_audience": target_audience.strip(),
        "research_objective": research_objective.strip(),
        "research_goal": research_objective.strip(),
        "industry": industry,
        "simulation_type": simulation_type,
        "persona_count": int(persona_count),
        "age": age.strip(),
        "gender": gender,
        "profession": profession.strip(),
        "location": location.strip(),
        "interests": interests.strip(),
    }


def render_workspace() -> None:
    render_page_header(
        "Synthetic User Generation Platform",
        "Create one experiment, generate personas once, and reuse the same session data throughout the workflow.",
    )

    personas = get_personas()
    experiment = get_experiment()
    survey_results = get_survey_results()

    if personas:
        st.success(f"{len(personas)} personas are stored in this session.")

    with st.form("workspace_form"):
        st.subheader("Experiment setup")
        col1, col2 = st.columns(2)
        with col1:
            experiment_name = st.text_input(
                "Experiment Name",
                value=experiment.get("experiment_name", ""),
                placeholder="Mobile banking onboarding study",
            )
            product_name = st.text_input(
                "Product Name",
                value=experiment.get("product_name", ""),
                placeholder="FinBank Mobile App",
            )
            industry = st.selectbox(
                "Industry",
                ["Technology", "Healthcare", "Finance", "Retail", "Education", "E-Commerce", "Travel", "Entertainment", "Other"],
                index=["Technology", "Healthcare", "Finance", "Retail", "Education", "E-Commerce", "Travel", "Entertainment", "Other"].index(
                    experiment.get("industry", "Technology")
                    if experiment.get("industry", "Technology") in ["Technology", "Healthcare", "Finance", "Retail", "Education", "E-Commerce", "Travel", "Entertainment", "Other"]
                    else "Technology"
                ),
            )
            simulation_type = st.selectbox(
                "Simulation Type",
                ["Customer Persona", "Employee Persona", "Patient Persona", "Student Persona", "Shopper Behavior", "General User"],
                index=["Customer Persona", "Employee Persona", "Patient Persona", "Student Persona", "Shopper Behavior", "General User"].index(
                    experiment.get("simulation_type", "Customer Persona")
                    if experiment.get("simulation_type", "Customer Persona") in ["Customer Persona", "Employee Persona", "Patient Persona", "Student Persona", "Shopper Behavior", "General User"]
                    else "Customer Persona"
                ),
            )
        with col2:
            description = st.text_area(
                "Description",
                value=experiment.get("description", ""),
                placeholder="Describe the product or concept.",
                height=110,
            )
            target_audience = st.text_area(
                "Target Audience",
                value=experiment.get("target_audience", ""),
                placeholder="Who should these personas represent?",
                height=110,
            )
            research_objective = st.text_area(
                "Research Objective",
                value=experiment.get("research_objective", ""),
                placeholder="What do you want to learn?",
                height=110,
            )

        st.subheader("Persona seed")
        seed_col1, seed_col2, seed_col3 = st.columns(3)
        with seed_col1:
            persona_count = st.number_input(
                "Persona Count",
                min_value=1,
                max_value=10,
                value=max(1, min(int(experiment.get("persona_count", 3) or 3), 10)),
                step=1,
            )
            age = st.text_input("Age", value=experiment.get("age", "25-35"))
        with seed_col2:
            gender_options = ["Mixed", "Female", "Male", "Non-binary"]
            gender = st.selectbox(
                "Gender",
                gender_options,
                index=gender_options.index(experiment.get("gender", "Mixed")) if experiment.get("gender", "Mixed") in gender_options else 0,
            )
            profession = st.text_input("Profession", value=experiment.get("profession", "Software Engineer"))
        with seed_col3:
            location = st.text_input("Location", value=experiment.get("location", "India"))
            interests = st.text_area("Interests", value=experiment.get("interests", "Technology, AI, Shopping"), height=92)

        generate_clicked = st.form_submit_button("Generate Personas", use_container_width=True)

    if generate_clicked:
        required_fields = {
            "Experiment Name": experiment_name,
            "Product Name": product_name,
            "Description": description,
            "Target Audience": target_audience,
            "Research Objective": research_objective,
        }
        missing = [label for label, value in required_fields.items() if not str(value).strip()]
        if missing:
            st.error("Please complete: " + ", ".join(missing))
            return

        experiment_payload = build_experiment_payload(
            experiment_name=experiment_name,
            product_name=product_name,
            description=description,
            target_audience=target_audience,
            research_objective=research_objective,
            industry=industry,
            simulation_type=simulation_type,
            persona_count=int(persona_count),
            age=age,
            gender=gender,
            profession=profession,
            location=location,
            interests=interests,
        )
        st.session_state["experiment"] = experiment_payload

        try:
            with st.spinner("Generating personas with Gemini and Faker enrichment..."):
                generator = PersonaGenerator()
                generated_personas = generator.generate_personas(
                    age=experiment_payload["age"],
                    gender=experiment_payload["gender"],
                    profession=experiment_payload["profession"],
                    location=experiment_payload["location"],
                    interests=experiment_payload["interests"],
                    persona_count=experiment_payload["persona_count"],
                    product_name=experiment_payload["product_name"],
                    description=experiment_payload["description"],
                    target_audience=experiment_payload["target_audience"],
                    research_objective=experiment_payload["research_objective"],
                    industry=experiment_payload["industry"],
                    simulation_type=experiment_payload["simulation_type"],
                )
        except Exception as exc:
            st.error(f"Persona generation failed. Detail: {exc}")
            return

        if not generated_personas:
            st.error("No personas were generated. Please review the inputs and try again.")
            return

        save_personas(generated_personas)
        st.success(f"Successfully generated {len(generated_personas)} personas.")
        if generator.last_error:
            st.warning(generator.last_error)

        st.page_link("pages/persona_cards.py", label="Open Persona Cards")

    st.divider()
    st.subheader("Current session")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Personas", len(get_personas()))
    metric_col2.metric("Experiment", "Saved" if get_experiment() else "Pending")
    metric_col3.metric("Survey", "Complete" if survey_results else "Pending")
    metric_col4.metric("Responses", len(survey_results.get("responses", [])) if survey_results else 0)

    if get_experiment():
        with st.expander("Experiment configuration", expanded=False):
            st.json(get_experiment())

    current_personas = get_personas()
    if current_personas:
        with st.expander("Generated persona JSON preview", expanded=False):
            st.json(current_personas[:3])
        st.download_button(
            label="Download Personas JSON",
            data=json.dumps(current_personas, indent=2).encode("utf-8"),
            file_name="personas.json",
            mime="application/json",
        )


def main() -> None:
    st.set_page_config(page_title="Synthetic User Generation Platform", layout="wide")
    init_session_state()
    render_sidebar("Home / Workspace")
    render_workspace()


if __name__ == "__main__":
    main()
