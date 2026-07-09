import json
import os
from typing import List

os.environ.pop("GOOGLE_API_KEY", None)

from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from services.faker_service import generate_fake_details


# Load environment variables
load_dotenv()

# Use available API key without changing .env
GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)


# ----------------------------
# Pydantic Models
# ----------------------------

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
    pain_points: List[str] = Field(description="List of pain points")

    technology_usage: str
    buying_behavior: str

    psychological_profile: PsychologicalProfile
    behavior_pattern: BehaviorPattern
    big_five_personality: BigFivePersonality


class PersonaListContainer(BaseModel):
    personas: List[PersonaSchema]


# ----------------------------
# Persona Generator
# ----------------------------

class PersonaGenerator:

    def __init__(self):

        if not GEMINI_API_KEY:
            raise ValueError("Gemini API key not found")

        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )


    def generate_personas(
        self,
        age: str,
        gender: str,
        profession: str,
        location: str,
        interests: str,
        persona_count: int = 1,
    ):

        prompt = f"""
You are an expert UX researcher and behavioral psychologist.

Generate {persona_count} highly realistic, diverse and unique synthetic personas.

Each persona should contain:

- Name
- Age
- Gender
- Occupation
- Education
- Income
- Bio
- Goals
- Pain Points
- Technology Usage
- Buying Behavior
- Psychological Profile
- Behavior Pattern
- Big Five Personality


Target Criteria:

Age: {age}
Gender: {gender}
Profession: {profession}
Location: {location}
Interests: {interests}
"""


        try:

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": PersonaListContainer,
                },
            )


            raw_data = json.loads(response.text)

            personas = raw_data.get("personas", [])


            if not personas:
                return []


            enriched_personas = []


            for persona in personas:

                fake_details = generate_fake_details()

                enriched_persona = {
                    **persona,
                    **fake_details,
                }

                enriched_personas.append(
                    enriched_persona
                )


            return enriched_personas


        except Exception as e:

            print(
                f"Error generating personas: {e}"
            )

            return []
        
if __name__ == "__main__":

    generator = PersonaGenerator()

    personas = generator.generate_personas(
        age="25",
        gender="Female",
        profession="Software Engineer",
        location="India",
        interests="Technology, AI, Shopping",
        persona_count=1
    )

    print(json.dumps(personas, indent=4))