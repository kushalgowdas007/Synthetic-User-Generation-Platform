from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# ============================================================
# ENVIRONMENT / PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Loads local .env when running locally.
# Vercel production variables come from the Vercel environment.
load_dotenv(os.path.join(BASE_DIR, ".env"))


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Research Studio API",
    version="1.0.0",
    description="Synthetic User Generation & Product Decision Platform API",
)


# ============================================================
# HELPERS
# ============================================================

def gemini_is_configured() -> bool:
    """Return whether a Gemini/Google API key is available."""
    return bool(
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )


def safe_error_message(exc: Exception) -> str:
    """Convert exceptions to a readable API error without exposing secrets."""
    message = str(exc)

    # Avoid accidentally exposing API keys or sensitive values.
    for key_name in (
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        secret = os.getenv(key_name)

        if secret and secret in message:
            message = message.replace(secret, "[REDACTED]")

    return message


# ============================================================
# HEALTH & INFO
# ============================================================

@app.get("/api")
def api_root():
    return {
        "name": "AI Research Studio",
        "tagline": "From synthetic users to product decisions",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engine": "fastapi",
        "gemini_configured": gemini_is_configured(),
        "vercel_env": os.getenv("VERCEL_ENV", "local"),
    }


# ============================================================
# SURVEY TEMPLATES
# ============================================================

@app.get("/api/templates")
def get_survey_templates():
    try:
        from backend.services.survey_service import SURVEY_TEMPLATES

        return {
            "templates": list(SURVEY_TEMPLATES.keys()),
            "details": SURVEY_TEMPLATES,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load survey templates: {safe_error_message(exc)}",
        )


# ============================================================
# PERSONA GENERATION
# ============================================================

class PersonaGenerateRequest(BaseModel):
    product_name: str = ""
    description: str = ""
    target_audience: str = ""
    research_objective: str = ""
    industry: str = ""
    simulation_type: str = ""

    persona_count: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    age: str = "20-45"
    gender: str = "Diverse"
    profession: str = "Tech & Business"
    location: str = "Urban India / Global"
    interests: str = "Technology, Productivity, SaaS"

    experiment_name: str = "Product Validation Study"
    bypass_cache: bool = False


@app.post("/api/personas")
def generate_personas(req: PersonaGenerateRequest):
    try:
        from services.persona_generator import PersonaGenerator
        from services.persona_quality import (
            evaluate_persona_quality,
            evaluate_population_diversity,
        )

        generator = PersonaGenerator()

        cohort = generator.generate_personas(
            age=req.age,
            gender=req.gender,
            profession=req.profession,
            location=req.location,
            interests=req.interests,
            persona_count=req.persona_count,
            product_name=req.product_name,
            description=req.description,
            target_audience=req.target_audience,
            research_objective=req.research_objective,
            industry=req.industry,
            simulation_type=req.simulation_type,
            bypass_cache=req.bypass_cache,
        )

        if not cohort:
            last_error = getattr(
                generator,
                "last_error",
                None,
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    f"Persona generation returned no personas."
                    + (
                        f" Generator error: {last_error}"
                        if last_error
                        else ""
                    )
                ),
            )

        # Persona quality scoring
        for persona in cohort:
            quality_result = evaluate_persona_quality(
                persona,
                cohort,
            )

            persona["quality_score"] = quality_result.overall_score
            persona["needs_review"] = quality_result.needs_review
            persona["quality_warnings"] = quality_result.warnings

        # Population diversity
        diversity_report = evaluate_population_diversity(cohort)

        if hasattr(diversity_report, "to_dict"):
            diversity_data = diversity_report.to_dict()
        else:
            diversity_data = {
                "diversity_score": getattr(
                    diversity_report,
                    "diversity_score",
                    85,
                ),
                "is_low_diversity": getattr(
                    diversity_report,
                    "is_low_diversity",
                    False,
                ),
                "diversity_warnings": getattr(
                    diversity_report,
                    "diversity_warnings",
                    [],
                ),
            }

        return {
            "personas": cohort,
            "persona_count": len(cohort),
            "source": getattr(
                generator,
                "generation_source",
                "local_faker_fallback",
            ),
            "population_diversity": diversity_data,
            "last_error": getattr(
                generator,
                "last_error",
                None,
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Persona generation failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# SURVEY
# ============================================================

class SurveyExecuteRequest(BaseModel):
    personas: List[Dict[str, Any]]

    product_name: str = "the product"

    research_goal: str = (
        "Evaluate user interest, usability, and pricing perception"
    )

    template: str = "Product Adoption"

    custom_questions: Optional[
        List[Dict[str, Any]]
    ] = None


@app.post("/api/survey")
def run_survey(req: SurveyExecuteRequest):
    try:
        from backend.services.survey_service import execute_survey

        if not req.personas:
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one persona is required "
                    "to run a survey."
                ),
            )

        result = execute_survey(
            personas=req.personas,
            product_name=req.product_name,
            research_goal=req.research_goal,
            template_name=req.template or "Product Adoption",
            survey_questions=req.custom_questions,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Survey execution failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# INTERVIEW
# ============================================================

class InterviewRequest(BaseModel):
    persona: Dict[str, Any]
    question: str
    memory_payload: Optional[
        Dict[str, Any]
    ] = None
    experiment: Optional[
        Dict[str, Any]
    ] = None


@app.post("/api/interview")
def interview_persona(req: InterviewRequest):
    try:
        from services.interview_service import (
            generate_interview_reply,
            create_memory_payload,
        )

        memory = (
            req.memory_payload
            or create_memory_payload(req.persona)
        )

        experiment_context = (
            req.experiment
            or {
                "product_name": req.persona.get(
                    "company",
                    "Product",
                )
            }
        )

        result = generate_interview_reply(
            persona=req.persona,
            user_message=req.question,
            memory_payload=memory,
            experiment=experiment_context,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Interview step failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# FOCUS GROUP
# ============================================================

class FocusGroupRequest(BaseModel):
    question: str
    personas: List[Dict[str, Any]]
    experiment: Optional[
        Dict[str, Any]
    ] = None


@app.post("/api/focus-group")
def focus_group(req: FocusGroupRequest):
    try:
        from services.focus_group_service import run_focus_group

        if not req.personas:
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one persona is required "
                    "to run a focus group."
                ),
            )

        experiment = (
            req.experiment
            or {
                "product_name": "the product"
            }
        )

        transcript = run_focus_group(
            question=req.question,
            personas=req.personas,
            experiment=experiment,
        )

        return {
            "transcript": transcript
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Focus group execution failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# INSIGHTS
# ============================================================

class InsightsRequest(BaseModel):
    personas: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    survey_results: Optional[
        Dict[str, Any]
    ] = None

    interview_results: Optional[
        List[Dict[str, Any]]
    ] = None

    focus_group_results: Optional[
        List[Dict[str, Any]]
    ] = None

    experiment: Optional[
        Dict[str, Any]
    ] = None


@app.post("/api/insights")
def generate_insights(req: InsightsRequest):
    try:
        from services.insight_agent import (
            extract_research_insights
        )

        survey = (
            req.survey_results
            or {
                "responses": [],
                "product_fit_score": 65.0,
            }
        )

        interviews = (
            req.interview_results
            or []
        )

        focus_group = (
            req.focus_group_results
            or []
        )

        experiment = (
            req.experiment
            or {
                "product_name": "the product"
            }
        )

        insights = extract_research_insights(
            personas=req.personas,
            survey_results=survey,
            interview_rows=interviews,
            focus_rows=focus_group,
            experiment=experiment,
        )

        return insights

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Insight synthesis failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# ACTION / DECISION ENGINE
# ============================================================

class ActionRequest(BaseModel):
    experiment: Dict[str, Any] = Field(
        default_factory=dict
    )

    personas: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    insights: Optional[
        Dict[str, Any]
    ] = None

    survey_results: Optional[
        Dict[str, Any]
    ] = None


@app.post("/api/actions")
def get_actions(req: ActionRequest):
    try:
        from services.action_engine import ActionEngine
        from services.decision_engine import (
            generate_product_actions
        )

        decisions = ActionEngine.generate_decisions(
            experiment=req.experiment,
            personas=req.personas,
            insights=req.insights,
            survey_results=req.survey_results,
        )

        if not decisions:
            decisions = generate_product_actions(
                insights_data=req.insights,
                personas=req.personas,
                experiment=req.experiment,
            )

        return {
            "actions": decisions
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Action generation failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# EXPERIMENT SIMULATION
# ============================================================

class SimulationRequest(BaseModel):
    baseline_fit: float = 65.0

    pricing_strategy: str = (
        "Standard Paid"
    )

    trust_signals: bool = True

    onboarding_friction_reduction: int = Field(
        default=50,
        ge=0,
        le=100,
    )

    automation_added: bool = True

    trial_bonus: int = Field(
        default=15,
        ge=0,
        le=50,
    )

    guarantee_offered: bool = False


@app.post("/api/simulation")
def simulate_experiment(
    req: SimulationRequest,
):
    try:
        base_fit = max(
            0.0,
            min(
                100.0,
                float(req.baseline_fit),
            ),
        )

        delta = 0.0
        factors: List[Dict[str, Any]] = []

        # Pricing
        if req.pricing_strategy == "Freemium / Free Trial":
            delta += 12.0
            factors.append({
                "factor": "Freemium / Free Trial Model",
                "impact": "+12.0 pts",
            })

        elif req.pricing_strategy == "Discounted / Subsidy":
            delta += 8.0
            factors.append({
                "factor": "Discounted Pricing",
                "impact": "+8.0 pts",
            })

        elif req.pricing_strategy == "Enterprise Custom":
            delta -= 5.0
            factors.append({
                "factor": "Enterprise Custom Complexity",
                "impact": "-5.0 pts",
            })

        else:
            factors.append({
                "factor": "Standard Pricing Baseline",
                "impact": "+0.0 pts",
            })

        # Trust
        if req.trust_signals:
            delta += 8.0

            factors.append({
                "factor": "Trust & Security Signals",
                "impact": "+8.0 pts",
            })

        # Automation
        if req.automation_added:
            delta += 7.0

            factors.append({
                "factor": "AI Assistant Automation",
                "impact": "+7.0 pts",
            })

        # Guarantee
        if req.guarantee_offered:
            delta += 5.0

            factors.append({
                "factor": "Money-Back Guarantee",
                "impact": "+5.0 pts",
            })

        # Onboarding
        onboarding_impact = (
            req.onboarding_friction_reduction
            / 100.0
        ) * 10.0

        delta += onboarding_impact

        factors.append({
            "factor": (
                "Onboarding Streamlining "
                f"({req.onboarding_friction_reduction}%)"
            ),
            "impact": (
                f"+{onboarding_impact:.1f} pts"
            ),
        })

        # Trial
        trial_impact = (
            req.trial_bonus
            / 50.0
        ) * 6.0

        delta += trial_impact

        factors.append({
            "factor": (
                f"Trial Duration Bonus "
                f"({req.trial_bonus}%)"
            ),
            "impact": (
                f"+{trial_impact:.1f} pts"
            ),
        })

        simulated_fit = round(
            min(
                100.0,
                max(
                    0.0,
                    base_fit + delta,
                ),
            ),
            1,
        )

        predicted_adoption = round(
            min(
                98.0,
                simulated_fit * 0.88,
            ),
            1,
        )

        return {
            "label": "Simulated estimate",
            "disclaimer": (
                "Not a production forecast. "
                "Predictions are model-derived "
                "synthetic approximations."
            ),
            "baseline_fit": base_fit,
            "simulated_fit": simulated_fit,
            "delta": round(delta, 1),
            "predicted_adoption_rate": predicted_adoption,
            "factors": factors,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Simulation failed: "
                f"{safe_error_message(exc)}"
            ),
        )


# ============================================================
# REPORTS
# ============================================================

class ReportRequest(BaseModel):
    experiment: Dict[str, Any] = Field(
        default_factory=dict
    )

    personas: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    survey_results: Optional[
        Dict[str, Any]
    ] = None

    interview_rows: Optional[
        List[Dict[str, Any]]
    ] = None

    insights: Optional[
        Dict[str, Any]
    ] = None

    focus_group: Optional[
        List[Dict[str, Any]]
    ] = None


@app.post("/api/reports")
def generate_reports(req: ReportRequest):
    try:
        from services.consultant_service import (
            build_consultant_report
        )

        from services.report_service import (
            export_markdown_report
        )

        consultant_report = build_consultant_report(
            experiment=req.experiment,
            insights=req.insights,
            survey=req.survey_results,
            focus_group=req.focus_group or [],
            personas=req.personas,
        )

        markdown_report = export_markdown_report(
            experiment=req.experiment,
            personas=req.personas,
            survey_results=req.survey_results,
            interview_rows=req.interview_rows or [],
            insights=req.insights,
            consultant_report=consultant_report,
        )

        return {
            "markdown": markdown_report,
            "consultant_report": consultant_report,
            "generated_at": consultant_report.get(
                "generated_at"
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Report generation failed: "
                f"{safe_error_message(exc)}"
            ),
        )