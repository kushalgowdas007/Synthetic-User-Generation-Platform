import json
from google import genai
from pydantic import BaseModel, Field
from typing import List

# Import your API key configuration safely
from config.settings import GEMINI_API_KEY


class PsychologicalProfile(BaseModel):
    motivation: str
    values: str
    decision_style: str
    risk_tolerance: str
    emotional_traits: str


class BehaviorPattern(BaseModel):
    shopping: str
    communication: str
    social_media: str
    daily_routine: str
    brand_loyalty: str


class BigFivePersonality(BaseModel):
    openness: str
    conscientiousness: str
    extraversion: str
    agreeableness: str
    neuroticism: str


class PersonaSchema(BaseModel):
    name: str
    age: int
    gender: str
    occupation: str
    education: str
    income: str
    bio: str
    goals: List[str] = Field(description="List of core goals")
    pain_points: List[str] = Field(description="List of main pain points")
    technology_usage: str
    buying_behavior: str
    psychological_profile: PsychologicalProfile
    behavior_pattern: BehaviorPattern
    big_five_personality: BigFivePersonality


class PersonaListContainer(BaseModel):
    personas: List[PersonaSchema]


class PersonaGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_personas(
        self,
        age: str,
        gender: str,
        profession: str,
        location: str,
        interests: str,
        persona_count: int = 1
    ):
        prompt = f"""
You are an expert UX researcher and behavioral psychologist.

Generate {persona_count} highly realistic, diverse, and distinct synthetic personas.
Each persona must be completely unique with distinct motivations, routines, and traits.

Target Criteria to base the generation on:
- Age bracket/Context: {age}
- Gender: {gender}
- Profession context: {profession}
- Location context: {location}
- Core Interests: {interests}
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": PersonaListContainer,
                    "temperature": 0.7
                }
            )

            raw_data = json.loads(response.text)

            return raw_data.get("personas", [])

        except Exception as e:
            print(f"Error generating personas inside service: {e}")
            return None