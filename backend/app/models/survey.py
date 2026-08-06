from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4


class Survey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    questions: List[str]
