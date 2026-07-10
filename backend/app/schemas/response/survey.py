from pydantic import BaseModel
from typing import List


class SurveyResponse(BaseModel):
    id: str
    title: str
    description: str
    questions: List[str]
    message: str


class SurveyExecutionResponse(BaseModel):
    survey_id: str
    total_personas: int
    responses: list
    message: str