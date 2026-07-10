from backend.app.services.survey_service import SurveyService
from backend.app.schemas.request.survey import CreateSurveyRequest


service = SurveyService()

request = CreateSurveyRequest(
    title="Shopping Survey",
    description="Understand shopping behaviour",
    questions=[
        "Do you shop online?",
        "How often do you buy?"
    ]
)

survey = service.create_survey(request)

print(survey)

result = service.execute_survey(
    survey.id,
    [
        "Student Persona",
        "Working Professional",
        "Senior Citizen"
    ]
)

print(result)