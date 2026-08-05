from services.persona_generator import PersonaGenerator


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
        assert 0 <= persona["validation_score"] <= 100
        assert 0 <= persona["completeness_score"] <= 100
        assert 0 <= persona["consistency_score"] <= 100
