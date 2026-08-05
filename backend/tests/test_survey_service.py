from backend.services.survey_service import (
    DEFAULT_SURVEY_QUESTIONS,
    SURVEY_TEMPLATES,
    analyze_survey_responses,
    create_survey,
    execute_survey,
)


def test_default_survey_questions_are_available():
    assert isinstance(DEFAULT_SURVEY_QUESTIONS, list)
    assert len(DEFAULT_SURVEY_QUESTIONS) >= 3


def test_create_survey_returns_question_payload():
    survey = create_survey(product_name="FitPulse AI", research_goal="Retention")
    assert len(survey) >= 3
    assert all("id" in question and "question" in question for question in survey)


def test_execute_survey_returns_response_rows():
    personas = [
        {
            "name": "Aarav",
            "occupation": "Student",
            "goals": ["Stay healthy"],
            "pain_points": ["Low motivation"],
            "technology_usage": "High",
            "big_five": {"openness": 80, "conscientiousness": 70, "extraversion": 60, "agreeableness": 65, "neuroticism": 30},
        }
    ]

    result = execute_survey(personas=personas, product_name="FitPulse AI", research_goal="Retention")

    assert "responses" in result
    assert len(result["responses"]) == 3
    assert all("question_id" in response for response in result["responses"])


def test_survey_templates_and_analytics_are_available():
    assert "Pricing Sensitivity" in SURVEY_TEMPLATES
    survey = create_survey(
        product_name="FitPulse AI",
        research_goal="Retention",
        template_name="Pricing Sensitivity",
        include_dynamic_questions=True,
    )
    assert len(survey) > len(DEFAULT_SURVEY_QUESTIONS)
    assert all("category" in question for question in survey)

    result = execute_survey(
        personas=[{"name": "Meera", "technology_usage": "High", "goals": ["Save time"], "pain_points": ["High cost"]}],
        product_name="FitPulse AI",
        research_goal="Retention",
        template_name="Pricing Sensitivity",
        include_dynamic_questions=True,
    )
    analytics = analyze_survey_responses(result["responses"])
    assert analytics["response_count"] == len(result["responses"])
    assert analytics["average_by_category"]
