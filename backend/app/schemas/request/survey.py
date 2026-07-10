from pydantic import BaseModel
from typing import List, Optional


class CreateSurveyRequest(BaseModel):
    title: str
    description: str
    questions: List[str]


class UpdateSurveyRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    questions: Optional[List[str]] = None