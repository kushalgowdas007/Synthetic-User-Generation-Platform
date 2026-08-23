import pytest
from services.persona_generator import PersonaGenerator
from services.persona_quality import (
    evaluate_persona_quality,
    evaluate_population_diversity,
)


def test_persona_generator_adds_quality_dimensions():
    generator = PersonaGenerator()
    generator._gemini_available = False

    personas = generator.generate_personas(
        age="25-35",
        gender="Mixed",
        profession="Software Engineer",
        location="India",
        interests="AI, productivity",
        persona_count=3,
        product_name="FitPulse AI",
        research_objective="Understand adoption barriers",
    )

    assert len(personas) == 3
    for persona in personas:
        assert 0 <= persona["quality_score"] <= 100
        assert 0 <= persona["diversity_score"] <= 100
        assert 0 <= persona["completeness_score"] <= 100
        assert persona["quality_status"] in ("Valid", "Needs Review")


def test_persona_quality_diagnostics_and_warnings():
    # Flawed persona: age < 22 but senior director, low tech but API early adopter
    flawed_persona = {
        "name": "Young Director",
        "age": 19,
        "gender": "Male",
        "occupation": "Chief Executive Director",
        "education": "High School",
        "income": "INR 50 LPA",
        "bio": "Short",
        "goals": ["Only one goal"],
        "pain_points": [],
        "technology_usage": "Low",
        "buying_behavior": "Early adopter API automation-first",
        "psychological_profile": {},
        "behavior_pattern": {},
        "big_five_personality": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
    }

    report = evaluate_persona_quality(flawed_persona)
    assert report.overall_score < 70
    assert report.status == "Needs Review"
    assert len(report.warnings) >= 3


def test_population_diversity_evaluation():
    diverse_cohort = [
        {"age": 22, "gender": "Female", "occupation": "Student", "technology_usage": "Mobile-first", "buying_behavior": "Budget-first"},
        {"age": 34, "gender": "Male", "occupation": "Product Manager", "technology_usage": "Advanced", "buying_behavior": "ROI-focused"},
        {"age": 52, "gender": "Female", "occupation": "Clinic Director", "technology_usage": "Medium", "buying_behavior": "Trust-first"},
    ]
    report = evaluate_population_diversity(diverse_cohort)
    assert report.diversity_score > 50
    assert report.status == "Good Diversity"
