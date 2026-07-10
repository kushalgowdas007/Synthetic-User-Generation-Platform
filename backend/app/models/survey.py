from pydantic import BaseModel
from typing import List
from uuid import uuid4


class Survey(BaseModel):
    id: str = str(uuid4())
    title: str
    description: str
    questions: List[str]