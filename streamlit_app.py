from __future__ import annotations

import json
from typing import Any, Dict

import streamlit as st
from frontend.shared import (
    get_experiment,
    get_experiment_history,
    get_insights,
    get_interview_results,
    get_personas,
    get_survey_results,
    init_session_state,
    render_page_header,
    render_sidebar,
    render_synthetic_disclaimer,
    save_experiment_snapshot,
    save_personas,
)
from services.persona_generator import PersonaGenerator
from services.workspace_store import list_workspaces, load_workspace, save_workspace


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


def render_experiment_history() -> None:
    history = get_experiment_history()
    if not history:
        return

    st.subheader("Recent Experiments")
    recent_rows = [
        {
            "Experiment": item.get("experiment_name", "Untitled"),
            "Product": item.get("product_name", "N/A"),
            "Industry": item.get("industry", "N/A"),
            "Personas": item.get("persona_count_generated", 0),
            "Updated": item.get("updated_at", ""),
        }
        for item in history[:6]
    ]
    st.dataframe(recent_rows, use_container_width=True, hide_index=True)

    with st.expander("Experiment history actions", expanded=False):
        for item in history[:6]:
            experiment_id = str(item.get("experiment_id", item.get("experiment_name", "")))
            label = f"{item.get('experiment_name', 'Untitled')} - {item.get('product_name', 'N/A')}"
            row_col1, row_col2, row_col3 = st.columns([3, 1, 1])
            row_col1.write(label)
            if row_col2.button("Duplicate", key=f"duplicate_{experiment_id}", use_container_width=True):
                duplicated = dict(item)
                duplicated.pop("experiment_id", None)
                duplicated.pop("created_at", None)
                duplicated["experiment_name"] = f"{duplicated.get('experiment_name', 'Experiment')} Copy"
                save_experiment_snapshot(duplicated, get_personas())
                st.success("Experiment duplicated and loaded into the workspace form.")
                st.rerun()
            if row_col3.button("Delete", key=f"delete_{experiment_id}", use_container_width=True):
                remaining = [entry for entry in get_experiment_history() if str(entry.get("experiment_id")) != experiment_id]
                st.session_state["experiment_history"] = remaining
                if str(get_experiment().get("experiment_id")) == experiment_id:
                    st.session_state["experiment"] = {}
                st.success("Experiment removed from recent history.")
                st.rerun()


def render_workspace() -> None:
    render_page_header(
        "AI Research Studio",
        "A complete AI research workflow—from a product brief to an executive launch decision.",
        active_stage="Workspace",
    )

    hero_left, hero_right = st.columns([3, 1])
    with hero_left:
        st.caption("Research Copilot → Personas → Survey → Interviews → Focus Group → Insights → Executive Decision")
    with hero_right:

        if st.button("Load demo brief", use_container_width=True):
            st.session_state["experiment"] = {
                "experiment_name": "Orbit launch validation",
                "product_name": "Orbit",
                "description": "An AI workspace that turns scattered product feedback into clear product decisions.",
                "target_audience": "Startup product managers and UX researchers in India",
                "research_objective": "Validate adoption barriers, trust, and willingness to pay.",
                "research_goal": "Validate adoption barriers, trust, and willingness to pay.",
                "industry": "Technology",
                "simulation_type": "Customer Persona",
                "persona_count": 4,
                "age": "24-45",
                "gender": "Mixed",
                "profession": "Product Manager",
                "location": "India",
                "interests": "AI, product discovery, productivity",
            }
            st.session_state["toast_message"] = "Demo brief loaded. Generate personas when ready."
        if st.button("🚀 Load Demo Research Session", use_container_width=True):
            exp = {"experiment_name":"AI Personal Finance Assistant", "product_name":"Orbit Money", "description":"An automated AI personal finance assistant that budgets and optimizes investments.", "target_audience":"Young working professionals in urban tech hubs", "research_objective":"Validate trust, data privacy concerns, and willingness to pay monthly subscription.", "research_goal":"Validate trust, data privacy concerns, and willingness to pay monthly subscription.", "industry":"Finance", "simulation_type":"Customer Persona", "persona_count":4, "age":"24-38", "gender":"Mixed", "profession":"Software Engineer, Analyst, Designer", "location":"India", "interests":"Fintech, Investing, AI"}
            demo_personas = [
                {"id":"demo_1", "name":"Aarav Sharma", "age":28, "gender":"Male", "occupation":"Software Engineer", "education":"Bachelor's degree", "income":"INR 14-20 LPA", "bio":"Aarav is an ambitious software engineer interested in automated wealth management.", "goals":["Automate monthly savings", "Track investments"], "pain_points":["Lack of data privacy trust", "High subscription cost"], "technology_usage":"High", "buying_behavior":"Compares features before paying", "quality_score":92, "big_five_personality":{"openness":82, "conscientiousness":78, "extraversion":55, "agreeableness":65, "neuroticism":35}},
                {"id":"demo_2", "name":"Priya Nair", "age":31, "gender":"Female", "occupation":"Product Manager", "education":"Master's degree", "income":"INR 18-25 LPA", "bio":"Priya is a busy product manager seeking low-friction financial planning.", "goals":["Save time on budgeting", "Get personalized insights"], "pain_points":["Complex onboarding", "Hidden fees"], "technology_usage":"High", "buying_behavior":"Prefers free trial before committing", "quality_score":88, "big_five_personality":{"openness":75, "conscientiousness":85, "extraversion":70, "agreeableness":80, "neuroticism":25}}
            ]
            st.session_state["experiment"] = exp
            st.session_state["personas"] = demo_personas
            st.session_state["toast_message"] = "Full AI Personal Finance demo research loaded into workspace!"
            st.rerun()

    personas = get_personas()
    experiment = get_experiment()
    survey_results = get_survey_results()

    with st.expander("Saved workspaces", expanded=False):
        saved_workspaces = list_workspaces()
        if saved_workspaces:
            labels = {
                record["id"]: f"{record.get('experiment', {}).get('experiment_name', 'Untitled')} — {record.get('saved_at', '')[:19]}"
                for record in saved_workspaces
            }
            selected_id = st.selectbox("Experiment history", list(labels), format_func=labels.get)
            if st.button("Load selected workspace"):
                record = load_workspace(selected_id)
                if record:
                    st.session_state["experiment"] = record.get("experiment", {})
                    st.session_state["personas"] = record.get("personas", [])
                    st.session_state["survey_results"] = record.get("survey_results") or None
                    st.session_state["interview_results"] = record.get("interview_results", [])
                    st.session_state["insights"] = record.get("insights") or None
                    st.session_state["persona_memories"] = record.get("persona_memories", {})
                    st.session_state["research_plan"] = record.get("research_plan") or None
                    st.session_state["focus_group_results"] = record.get("focus_group_results", [])
                    st.session_state["consultant_report"] = record.get("consultant_report") or None
                    st.success("Workspace loaded into this session.")
                    st.rerun()
        else:
            st.caption("No saved workspaces yet.")

        if experiment and st.button("Save current workspace"):
            try:
                save_workspace(
                    experiment=experiment,
                    personas=personas,
                    survey_results=survey_results,
                    interview_results=get_interview_results(),
                    insights=get_insights(),
                    persona_memories=st.session_state.get("persona_memories", {}),
                    research_plan=st.session_state.get("research_plan") or {},
                    focus_group_results=st.session_state.get("focus_group_results", []),
                    consultant_report=st.session_state.get("consultant_report") or {},
                )
                st.success("Workspace saved. It is now available in experiment history.")
            except (OSError, ValueError) as exc:
                st.error(f"Unable to save workspace. Detail: {exc}")

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
                value=max(1, min(int(experiment.get("persona_count", 4) or 4), 10)),
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
        experiment_payload = save_experiment_snapshot(experiment_payload, [])
        
        # Phase 1: Compute Experiment Signature for Caching
        from services.cache_service import compute_experiment_signature, record_performance_metric
        from services.persona_quality import evaluate_persona_quality, evaluate_population_diversity
        import time

        try:
            progress = st.progress(0, text="Preparing persona generation request")
            exp_sig = compute_experiment_signature(experiment_payload)
            st.session_state["experiment_signature"] = exp_sig

            cached_personas = (
                st.session_state.get("cached_personas_store", {}).get(exp_sig)
            )

            start_time = time.time()
            generator = None

            if cached_personas:
                generated_personas = cached_personas
                st.info("⚡ Loaded from cache — Gemini call avoided.")
                record_performance_metric(
                    "persona_generation",
                    time.time() - start_time,
                    cache_hit=True,
                )
            else:
                st.info("✨ Generating new personas...")
                with st.spinner(
                    "Generating personas with Gemini batch generation and Faker enrichment..."
                ):
                    progress.progress(20, text="Validating experiment context")
                    generator = PersonaGenerator()
                    progress.progress(45, text="Generating persona profiles")
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
                    progress.progress(
                        90,
                        text="Scoring quality and population diversity",
                    )

                st.session_state.setdefault("cached_personas_store", {})[exp_sig] = (
                    generated_personas
                )
                record_performance_metric(
                    "persona_generation",
                    time.time() - start_time,
                    cache_hit=False,
                )
        except Exception as exc:
            st.error(f"Persona generation failed. Detail: {exc}")
            return


        if not generated_personas:
            st.error("No personas were generated. Please review the inputs and try again.")
            return

        # Evaluate quality scores & population diversity
        for p in generated_personas:
            q_eval = evaluate_persona_quality(p, generated_personas)
            p["quality_score"] = q_eval.overall_score
            p["needs_review"] = q_eval.needs_review
            p["quality_warnings"] = q_eval.warnings

        div_report = evaluate_population_diversity(generated_personas)
        if div_report.is_low_diversity:
            for w in div_report.diversity_warnings:
                st.warning(w)

        save_personas(generated_personas)
        save_experiment_snapshot(experiment_payload, generated_personas)
        if "progress" in locals():
            progress.progress(100, text="Personas ready")

        if generator is not None:
            source = getattr(generator, "generation_source", "Gemini")
            last_error = getattr(generator, "last_error", None)
            st.success(
                f"Successfully generated {len(generated_personas)} synthetic personas "
                f"({source}). Population Diversity Score: {div_report.diversity_score}/100"
            )
            if last_error:
                st.warning(last_error)
        else:
            st.success(
                f"Successfully loaded {len(generated_personas)} cached synthetic personas. "
                f"Population Diversity Score: {div_report.diversity_score}/100"
            )


            st.warning(generator.last_error)

        st.page_link("pages/persona_cards.py", label="Open Persona Cards")

    st.divider()
    st.subheader("Current session")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("Personas", len(get_personas()))
    metric_col2.metric("Experiment", "Saved" if get_experiment() else "Pending")
    metric_col3.metric("Survey", "Complete" if survey_results else "Pending")
    metric_col4.metric("Responses", len(survey_results.get("responses", [])) if survey_results else 0)
    if not get_experiment():
        st.info("Start with Research Copilot for a guided research blueprint, or load the demo brief for a fast walkthrough.")
        st.page_link("pages/research_copilot.py", label="Open Research Copilot")

    if get_experiment():
        with st.expander("Experiment configuration", expanded=False):
            st.json(get_experiment())
        with st.expander("Experiment metadata", expanded=False):
            metadata = {
                "experiment_id": get_experiment().get("experiment_id", "N/A"),
                "created_at": get_experiment().get("created_at", "N/A"),
                "updated_at": get_experiment().get("updated_at", "N/A"),
                "persona_count_requested": get_experiment().get("persona_count", 0),
                "persona_count_generated": get_experiment().get("persona_count_generated", 0),
            }
            st.json(metadata)

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

    st.divider()
    render_synthetic_disclaimer()
    st.divider()
    render_experiment_history()


def main() -> None:
    st.set_page_config(page_title="Synthetic User Generation Platform", layout="wide")
    init_session_state()
    render_sidebar("Home / Workspace")
    render_workspace()


if __name__ == "__main__":
    main()