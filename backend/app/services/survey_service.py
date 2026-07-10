import random
from uuid import uuid4

from backend.app.models.survey import Survey
from backend.app.schemas.request.survey import (
    CreateSurveyRequest,
    UpdateSurveyRequest,
)
from backend.app.schemas.response.survey import (
    SurveyResponse,
    SurveyExecutionResponse,
)


class SurveyService:

    def __init__(self):
        self.surveys = {}
        self.responses = []

        # Sample responses (temporary until AI integration)
        self.sample_answers = [
            "Yes",
            "No",
            "Maybe",
            "Very Likely",
            "Unlikely",
            "Highly Interested",
            "Not Interested",
            "Depends on the Price",
            "Need More Information",
            "Would Recommend",
            "Would Not Recommend",
            "Satisfied",
            "Neutral",
            "Dissatisfied",
            "I would purchase it",
            "I might purchase it later",
            "It doesn't match my needs",
            "Looks promising",
            "I'd like to try it",
            "Not sure yet"
        ]

    # --------------------------------------------------
    # Create Survey
    # --------------------------------------------------

    def create_survey(self, request: CreateSurveyRequest):

        survey = Survey(
            id=str(uuid4()),
            title=request.title,
            description=request.description,
            questions=request.questions,
        )

        self.surveys[survey.id] = survey

        return SurveyResponse(
            id=survey.id,
            title=survey.title,
            description=survey.description,
            questions=survey.questions,
            message="Survey created successfully.",
        )

    # --------------------------------------------------
    # Update Survey
    # --------------------------------------------------

    def update_survey(self, survey_id: str, request: UpdateSurveyRequest):

        if survey_id not in self.surveys:
            raise ValueError("Survey not found.")

        survey = self.surveys[survey_id]

        if request.title is not None:
            survey.title = request.title

        if request.description is not None:
            survey.description = request.description

        if request.questions is not None:
            survey.questions = request.questions

        return SurveyResponse(
            id=survey.id,
            title=survey.title,
            description=survey.description,
            questions=survey.questions,
            message="Survey updated successfully.",
        )

    # --------------------------------------------------
    # Delete Survey
    # --------------------------------------------------

    def delete_survey(self, survey_id: str):

        if survey_id not in self.surveys:
            raise ValueError("Survey not found.")

        del self.surveys[survey_id]

        return {
            "message": "Survey deleted successfully."
        }

    # --------------------------------------------------
    # Execute Survey
    # --------------------------------------------------

    def execute_survey(self, survey_id: str, personas: list):

        if survey_id not in self.surveys:
            raise ValueError("Survey not found.")

        survey = self.surveys[survey_id]

        results = []

        for persona in personas:

            persona_answers = []

            for question in survey.questions:

                answer = {
                    "question": question,
                    "answer": random.choice(self.sample_answers)
                }

                persona_answers.append(answer)

                self.track_response(
                    persona,
                    question,
                    answer["answer"]
                )

            results.append(
                {
                    "persona": persona,
                    "answers": persona_answers,
                }
            )

        return SurveyExecutionResponse(
            survey_id=survey.id,
            total_personas=len(personas),
            responses=results,
            message="Survey executed successfully.",
        )

    # --------------------------------------------------
    # Track Responses
    # --------------------------------------------------

    def track_response(self, persona, question, answer):

        self.responses.append(
            {
                "persona": persona,
                "question": question,
                "answer": answer,
            }
        )

    # --------------------------------------------------
    # Get All Responses
    # --------------------------------------------------

    def get_responses(self):
        return self.responses

    # --------------------------------------------------
    # Get Survey by ID (Optional)
    # --------------------------------------------------

    def get_survey(self, survey_id: str):

        if survey_id not in self.surveys:
            raise ValueError("Survey not found.")

        return self.surveys[survey_id]

    # --------------------------------------------------
    # Get All Surveys (Optional)
    # --------------------------------------------------

    def get_all_surveys(self):
        return list(self.surveys.values())