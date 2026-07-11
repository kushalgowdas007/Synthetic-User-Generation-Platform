from backend.services.survey_service import (
    DEFAULT_SURVEY_QUESTIONS,
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
