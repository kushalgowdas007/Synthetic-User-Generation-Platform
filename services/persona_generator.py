from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Mapping, Optional
from uuid import uuid4

from dotenv import load_dotenv
from faker import Faker
from pydantic import BaseModel, Field, ValidationError, field_validator

from services.faker_service import generate_fake_details

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - optional dependency guard
    genai = None
    types = None


load_dotenv()

logger = logging.getLogger(__name__)
fake = Faker("en_IN")

REQUIRED_FIELDS = [
    "name",
    "age",
    "gender",
    "occupation",
    "education",
    "income",
    "bio",
    "goals",
    "pain_points",
    "technology_usage",
    "buying_behavior",
    "psychological_profile",
    "behavior_pattern",
    "big_five_personality",
    "email",
    "phone",
    "address",
    "city",
    "company",
    "state",
    "pincode",
]


class PsychologicalProfileModel(BaseModel):
    motivation: str = "Practical progress"
    values: str = "Trust, value, convenience"
    decision_style: str = "Research-led"
    risk_tolerance: str = "Moderate"
    emotional_traits: str = "Curious and outcome-focused"


class BehaviorPatternModel(BaseModel):
    shopping: str = "Compares alternatives"
    communication: str = "Prefers concise communication"
    social_media: str = "Uses social proof selectively"
    daily_routine: str = "Balances work and personal goals"
    brand_loyalty: str = "Loyal when value remains clear"


class BigFiveModel(BaseModel):
    openness: int = Field(default=65, ge=0, le=100)
    conscientiousness: int = Field(default=65, ge=0, le=100)
    extraversion: int = Field(default=55, ge=0, le=100)
    agreeableness: int = Field(default=65, ge=0, le=100)
    neuroticism: int = Field(default=35, ge=0, le=100)


class GeneratedPersonaModel(BaseModel):
    name: str
    age: int = Field(ge=18, le=80)
    gender: str
    occupation: str
    education: str
    income: str
    bio: str
    goals: List[str]
    pain_points: List[str]
    technology_usage: str
    buying_behavior: str
    psychological_profile: PsychologicalProfileModel
    behavior_pattern: BehaviorPatternModel
    big_five_personality: BigFiveModel
    lifestyle: str = "Balanced and practical"
    motivation: str = "Improve daily outcomes"
    frustrations: List[str] = Field(default_factory=list)
    daily_routine: str = "Structured around work and personal commitments"
    decision_making: str = "Compares value, trust, and effort before committing"

    @field_validator("goals", "pain_points", "frustrations", mode="before")
    @classmethod
    def _listify(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, tuple):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, Mapping):
            return [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
        return [item.strip() for item in str(value).split(",") if item.strip()]


class PersonaListModel(BaseModel):
    personas: List[GeneratedPersonaModel]


class PersonaGenerator:
    """Canonical Gemini + Faker persona generator with validation and fallback safety."""

    def __init__(self, model_name: str = "gemini-2.5-flash", max_retries: int = 3) -> None:
        self.model_name = os.getenv("GEMINI_MODEL", model_name)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.max_retries = max(1, int(max_retries))
        self.last_error: Optional[str] = None
        self._gemini_available = bool(self.api_key and genai is not None and types is not None)
        self.client = genai.Client(api_key=self.api_key) if self._gemini_available else None

    def generate_personas(
        self,
        age: str,
        gender: str,
        profession: str,
        location: str,
        interests: str,
        persona_count: int = 1,
        product_name: str = "",
        description: str = "",
        target_audience: str = "",
        research_objective: str = "",
        industry: str = "",
        simulation_type: str = "",
    ) -> List[Dict[str, Any]]:
        self.last_error = None
        count = max(1, min(int(persona_count or 1), 10))

        context = {
            "age": age,
            "gender": gender,
            "profession": profession,
            "location": location,
            "interests": interests,
            "persona_count": count,
            "product_name": product_name,
            "description": description,
            "target_audience": target_audience,
            "research_objective": research_objective,
            "industry": industry,
            "simulation_type": simulation_type,
        }

        generated: List[Dict[str, Any]] = []
        if self._gemini_available:
            try:
                generated = self._generate_with_gemini(**context)
            except Exception as exc:
                self.last_error = f"Gemini generation failed after retries. Local personas were generated instead. Detail: {exc}"
                logger.exception("Gemini persona generation failed")
        else:
            if not self.api_key:
                self.last_error = "GEMINI_API_KEY was not found. Local Faker-backed personas were generated."
            else:
                self.last_error = "google-genai is unavailable. Local Faker-backed personas were generated."

        normalized = [self._normalize_persona(persona, index) for index, persona in enumerate(generated[:count])]
        while len(normalized) < count:
            normalized.append(self._build_fallback_persona(index=len(normalized), **context))

        return self._deduplicate_and_score(normalized, context)[:count]

    def _generate_with_gemini(self, **context: Any) -> List[Dict[str, Any]]:
        prompt = self._build_prompt(**context)
        last_error: Optional[Exception] = None

        for model_name in self._model_candidates():
            for attempt in range(self.max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=(
                                "You are a senior UX researcher, consumer psychologist, and behavioral scientist. "
                                "Return strict JSON only. Do not include markdown."
                            ),
                            response_mime_type="application/json",
                        ),
                    )
                    payload = self._loads_json(response.text)
                    parsed = self._validate_payload(payload)
                    self.model_name = model_name
                    return [persona.model_dump() for persona in parsed.personas]
                except Exception as exc:
                    last_error = exc
                    if attempt < self.max_retries - 1:
                        time.sleep(0.5 * (2**attempt))
            logger.warning("Model %s failed persona generation: %s", model_name, last_error)

        raise last_error or RuntimeError("Gemini generation failed")

    def _validate_payload(self, payload: Any) -> PersonaListModel:
        if isinstance(payload, list):
            payload = {"personas": payload}
        if not isinstance(payload, Mapping):
            raise ValueError("Gemini response was not a JSON object or list")

        try:
            return PersonaListModel.model_validate(payload)
        except ValidationError:
            repaired = self._repair_persona_payload(payload)
            return PersonaListModel.model_validate(repaired)

    def _repair_persona_payload(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        raw_personas = payload.get("personas", [])
        if not isinstance(raw_personas, list):
            raw_personas = [raw_personas]

        repaired = []
        for index, item in enumerate(raw_personas):
            persona = dict(item) if isinstance(item, Mapping) else {}
            persona["name"] = self._coerce_text(persona.get("name"), fake.name())
            persona["age"] = self._coerce_age(persona.get("age"))
            persona["gender"] = self._coerce_text(persona.get("gender"), "Mixed")
            persona["occupation"] = self._coerce_text(persona.get("occupation"), "Working Professional")
            persona["education"] = self._coerce_text(persona.get("education"), "Bachelor's degree")
            persona["income"] = self._coerce_text(persona.get("income"), "INR 10-15 LPA")
            persona["bio"] = self._coerce_text(persona.get("bio"), f"{persona['name']} is a practical user who evaluates products carefully.")
            persona["goals"] = self._coerce_list(persona.get("goals")) or ["Save time", "Make confident decisions"]
            persona["pain_points"] = self._coerce_list(persona.get("pain_points")) or ["Too much friction", "Lack of trust"]
            persona["technology_usage"] = self._coerce_text(persona.get("technology_usage"), "Medium")
            persona["buying_behavior"] = self._coerce_text(persona.get("buying_behavior") or persona.get("buying_behaviour"), "Compares value before purchase")
            persona["psychological_profile"] = self._repair_psychological_profile(persona.get("psychological_profile"))
            persona["behavior_pattern"] = self._repair_behavior_pattern(persona.get("behavior_pattern"))
            persona["big_five_personality"] = self._normalize_big_five(persona.get("big_five_personality"))
            persona["lifestyle"] = self._coerce_text(persona.get("lifestyle"), "Balanced and practical")
            persona["motivation"] = self._coerce_text(persona.get("motivation"), "Improve daily outcomes")
            persona["frustrations"] = self._coerce_list(persona.get("frustrations")) or persona["pain_points"]
            persona["daily_routine"] = self._coerce_text(persona.get("daily_routine"), "Structured around work and personal commitments")
            persona["decision_making"] = self._coerce_text(persona.get("decision_making"), "Compares value, trust, and effort before committing")
            repaired.append(persona)

        return {"personas": repaired}

    def _build_prompt(self, **context: Any) -> str:
        return f"""
Generate exactly {context['persona_count']} realistic, diverse synthetic personas for product research.

Return strict JSON with this shape:
{{
  "personas": [
    {{
      "name": "string",
      "age": 30,
      "gender": "string",
      "occupation": "string",
      "education": "string",
      "income": "string",
      "bio": "string",
      "goals": ["string"],
      "pain_points": ["string"],
      "technology_usage": "Low | Medium | High | Mobile-first | Advanced",
      "buying_behavior": "string",
      "psychological_profile": {{
        "motivation": "string",
        "values": "string",
        "decision_style": "string",
        "risk_tolerance": "string",
        "emotional_traits": "string"
      }},
      "behavior_pattern": {{
        "shopping": "string",
        "communication": "string",
        "social_media": "string",
        "daily_routine": "string",
        "brand_loyalty": "string"
      }},
      "big_five_personality": {{
        "openness": 0,
        "conscientiousness": 0,
        "extraversion": 0,
        "agreeableness": 0,
        "neuroticism": 0
      }},
      "lifestyle": "string",
      "motivation": "string",
      "frustrations": ["string"],
      "daily_routine": "string",
      "decision_making": "string"
    }}
  ]
}}

Diversity requirements:
- Vary age, gender, occupation, income, education, city context, technology adoption, personality, goals, and pain points.
- Keep each persona internally consistent: income must fit occupation, technology usage must fit lifestyle, motivations must fit behavior.
- Big Five scores must be numeric from 0 to 100 and plausible for the bio.
- Do not duplicate names, occupations, or biographies.

Experiment:
- Product name: {context['product_name']}
- Description: {context['description']}
- Target audience: {context['target_audience']}
- Research objective: {context['research_objective']}
- Industry: {context['industry']}
- Simulation type: {context['simulation_type']}

Persona seed:
- Age: {context['age']}
- Gender: {context['gender']}
- Profession: {context['profession']}
- Location: {context['location']}
- Interests: {context['interests']}
"""

    def _build_fallback_persona(self, index: int, **context: Any) -> Dict[str, Any]:
        fake_details = generate_fake_details()
        persona_gender = self._fallback_gender(context["gender"], index)
        persona_name = fake.name_male() if persona_gender.lower() == "male" else fake.name_female()
        occupation = self._diverse_occupation(context["profession"], context["industry"], context["simulation_type"], index)
        product_label = str(context["product_name"]).strip() or "the product"
        interest_list = self._coerce_list(context["interests"]) or ["convenience", "quality", "technology"]
        objective = str(context["research_objective"]).strip() or "understand adoption potential"
        age = self._fallback_age(context["age"], index)
        tech_usage = ["Low", "Medium", "Medium-High", "High", "Mobile-first", "Advanced"][index % 6]
        openness = random.randint(55, 92)
        conscientiousness = random.randint(50, 92)
        neuroticism = random.randint(18, 62)

        persona = {
            "name": persona_name,
            "age": age,
            "gender": persona_gender,
            "occupation": occupation,
            "education": self._education_for_occupation(occupation),
            "income": self._income_for_age(age, occupation),
            "bio": (
                f"{persona_name} is a {age}-year-old {occupation} in {fake_details['city']} who is evaluating {product_label}. "
                f"They care about {interest_list[0]} and need clear proof that a new solution will reduce friction."
            ),
            "goals": [
                f"Use {product_label} to support {objective}",
                f"Save time while managing {interest_list[0]}",
                "Make confident decisions with reliable information",
            ],
            "pain_points": [
                "Too many choices slow down decisions",
                "Existing tools feel fragmented or hard to trust",
                "Time pressure makes it difficult to try new solutions",
            ],
            "technology_usage": tech_usage,
            "buying_behavior": [
                "Compares reviews and pricing before purchase",
                "Values clear ROI and trusted recommendations",
                "Prefers a low-risk trial before committing",
                "Adopts quickly when the value is obvious",
            ][index % 4],
            "psychological_profile": {
                "motivation": "Practical improvement and measurable progress",
                "values": "Trust, convenience, value, and reliability",
                "decision_style": "Research-led but willing to try low-friction options",
                "risk_tolerance": ["Low", "Moderate", "Moderate-high"][index % 3],
                "emotional_traits": "Curious, cautious, and outcome-focused",
            },
            "behavior_pattern": {
                "shopping": "Checks reviews and compares alternatives",
                "communication": "Prefers concise updates and direct benefits",
                "social_media": "Uses social proof to validate new choices",
                "daily_routine": "Balances work demands with short decision windows",
                "brand_loyalty": "Loyal when the experience remains reliable",
            },
            "big_five_personality": {
                "openness": openness,
                "conscientiousness": conscientiousness,
                "extraversion": random.randint(35, 82),
                "agreeableness": random.randint(50, 88),
                "neuroticism": neuroticism,
            },
            "lifestyle": "Busy, mobile-aware, and outcome-focused",
            "motivation": "Reduce friction and make better decisions",
            "frustrations": ["Unclear pricing", "Too many steps", "Low trust in generic claims"],
            "daily_routine": "Uses short planning windows between work and personal responsibilities",
            "decision_making": "Compares value, effort, trust signals, and peer proof before committing",
            **fake_details,
        }
        return self._normalize_persona(persona, index)

    def _normalize_persona(self, persona: Mapping[str, Any], index: int) -> Dict[str, Any]:
        fake_details = generate_fake_details()
        repaired = self._repair_persona_payload({"personas": [persona]})["personas"][0]
        model = GeneratedPersonaModel.model_validate(repaired)
        payload = model.model_dump()

        normalized = {
            "id": str(persona.get("id") or persona.get("persona_id") or uuid4()),
            **payload,
            "email": self._coerce_text(persona.get("email"), fake_details["email"]),
            "phone": self._coerce_text(persona.get("phone"), fake_details["phone"]),
            "address": self._coerce_text(persona.get("address"), fake_details["address"]),
            "city": self._coerce_text(persona.get("city"), fake_details["city"]),
            "company": self._coerce_text(persona.get("company"), fake_details["company"]),
            "state": self._coerce_text(persona.get("state"), fake_details["state"]),
            "pincode": self._coerce_text(persona.get("pincode") or persona.get("postcode"), fake_details["pincode"]),
        }
        normalized["quality_score"] = self._quality_score(normalized)
        normalized.update(self._quality_dimensions(normalized))
        return normalized

    def _deduplicate_and_score(self, personas: List[Dict[str, Any]], context: Mapping[str, Any]) -> List[Dict[str, Any]]:
        seen_names: set[str] = set()
        seen_bios: set[str] = set()
        unique: List[Dict[str, Any]] = []

        for index, persona in enumerate(personas):
            name_key = str(persona.get("name", "")).strip().lower()
            bio_key = str(persona.get("bio", "")).strip().lower()
            if name_key in seen_names or bio_key in seen_bios:
                persona = self._build_fallback_persona(index=index + 20, **context)
                name_key = str(persona["name"]).lower()
                bio_key = str(persona["bio"]).lower()
            seen_names.add(name_key)
            seen_bios.add(bio_key)
            persona["quality_score"] = self._quality_score(persona)
            persona.update(self._quality_dimensions(persona))
            unique.append(persona)

        return unique

    def _quality_score(self, persona: Mapping[str, Any]) -> int:
        completeness = sum(1 for field in REQUIRED_FIELDS if persona.get(field) not in (None, "", [], {})) / len(REQUIRED_FIELDS)
        consistency = 1.0
        age = self._coerce_age(persona.get("age"))
        occupation = str(persona.get("occupation", "")).lower()
        if age < 22 and any(role in occupation for role in ("senior", "director", "manager")):
            consistency -= 0.2
        if not self._coerce_list(persona.get("goals")) or not self._coerce_list(persona.get("pain_points")):
            consistency -= 0.2
        realism = 0.85 if len(str(persona.get("bio", ""))) > 80 else 0.65
        score = (completeness * 40) + (max(consistency, 0.0) * 35) + (realism * 25)
        return max(0, min(100, round(score)))

    def _quality_dimensions(self, persona: Mapping[str, Any]) -> Dict[str, int]:
        """Expose interpretable quality signals alongside the composite score."""
        completeness = sum(1 for field in REQUIRED_FIELDS if persona.get(field) not in (None, "", [], {})) / len(REQUIRED_FIELDS)
        age = self._coerce_age(persona.get("age"))
        occupation = str(persona.get("occupation", "")).lower()
        consistency = 92 if not (age < 22 and any(role in occupation for role in ("senior", "director", "manager"))) else 68
        realism = min(96, 60 + min(24, len(str(persona.get("bio", ""))) // 8) + (8 if len(self._coerce_list(persona.get("pain_points"))) >= 2 else 0))
        confidence = round((completeness * 55) + (consistency * .25) + (realism * .20))
        return {"persona_confidence_score": max(0, min(100, confidence)), "realism_score": realism, "consistency_score": consistency}

    def _model_candidates(self) -> List[str]:
        candidates = [self.model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
        unique_candidates: List[str] = []
        for candidate in candidates:
            if candidate and candidate not in unique_candidates:
                unique_candidates.append(candidate)
        return unique_candidates

    @staticmethod
    def _loads_json(text: str) -> Any:
        cleaned = str(text or "").strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start_candidates = [index for index in (cleaned.find("{"), cleaned.find("[")) if index >= 0]
            if not start_candidates:
                raise
            start = min(start_candidates)
            end = max(cleaned.rfind("}"), cleaned.rfind("]"))
            if end <= start:
                raise
            return json.loads(cleaned[start : end + 1])

    @staticmethod
    def _coerce_text(value: Any, default: str) -> str:
        if value is None:
            return default
        text = str(value).strip()
        return text or default

    @staticmethod
    def _coerce_age(value: Any) -> int:
        if isinstance(value, int):
            return max(18, min(value, 80))
        digits = re.findall(r"\d+", str(value or ""))
        if digits:
            return max(18, min(int(digits[0]), 80))
        return random.randint(22, 55)

    @staticmethod
    def _coerce_list(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, tuple):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, Mapping):
            return [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
        return [item.strip() for item in str(value).split(",") if item.strip()]

    @staticmethod
    def _coerce_mapping(value: Any) -> Dict[str, Any]:
        if isinstance(value, Mapping):
            return {str(key): item for key, item in value.items()}
        if value is None:
            return {}
        return {"summary": str(value)}

    @classmethod
    def _repair_psychological_profile(cls, value: Any) -> Dict[str, str]:
        source = cls._coerce_mapping(value)
        defaults = PsychologicalProfileModel().model_dump()
        return {key: cls._coerce_text(source.get(key), default) for key, default in defaults.items()}

    @classmethod
    def _repair_behavior_pattern(cls, value: Any) -> Dict[str, str]:
        source = cls._coerce_mapping(value)
        defaults = BehaviorPatternModel().model_dump()
        return {key: cls._coerce_text(source.get(key), default) for key, default in defaults.items()}

    @staticmethod
    def _normalize_big_five(value: Any) -> Dict[str, int]:
        keys = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        if not isinstance(value, Mapping):
            return {key: random.randint(40, 85) for key in keys}
        scores: Dict[str, int] = {}
        for key in keys:
            try:
                score = int(float(str(value.get(key, random.randint(40, 85))).replace("%", "").strip()))
            except ValueError:
                score = random.randint(40, 85)
            scores[key] = max(0, min(score, 100))
        return scores

    @staticmethod
    def _fallback_age(age: str, index: int) -> int:
        digits = [int(item) for item in re.findall(r"\d+", str(age or ""))]
        if len(digits) >= 2:
            low, high = min(digits[0], digits[1]), max(digits[0], digits[1])
            return random.randint(max(18, low), min(80, high))
        if len(digits) == 1:
            return max(18, min(80, digits[0] + (index % 5) - 2))
        return random.randint(22, 55)

    @staticmethod
    def _fallback_gender(gender: str, index: int) -> str:
        value = str(gender or "").strip()
        if value.lower() in {"male", "female", "non-binary"}:
            return value
        return ["Female", "Male", "Non-binary", "Female", "Male"][index % 5]

    @staticmethod
    def _diverse_occupation(profession: str, industry: str, simulation_type: str, index: int) -> str:
        if profession and index == 0:
            return profession.strip()
        industry_options = {
            "healthcare": ["Nurse", "Clinic Administrator", "Telehealth Coordinator"],
            "finance": ["Financial Analyst", "Branch Manager", "Insurance Advisor"],
            "education": ["Teacher", "Graduate Student", "Learning Designer"],
            "retail": ["Store Manager", "Category Analyst", "Customer Success Associate"],
            "technology": ["Product Manager", "UX Researcher", "Data Analyst", "Software Engineer"],
            "e-commerce": ["Marketplace Seller", "Growth Marketer", "Operations Lead"],
        }
        options = industry_options.get(str(industry or "").lower(), ["Working Professional", "Student", "Operations Associate", "Consultant"])
        if "student" in str(simulation_type or "").lower():
            options = ["Undergraduate Student", "Graduate Student", "Online Learner"]
        return options[index % len(options)]

    @staticmethod
    def _education_for_occupation(occupation: str) -> str:
        occupation_text = occupation.lower()
        if "student" in occupation_text:
            return "Currently pursuing a degree"
        if any(role in occupation_text for role in ("manager", "analyst", "engineer", "researcher")):
            return random.choice(["Bachelor's degree", "Master's degree", "Professional certification"])
        return random.choice(["Diploma", "Bachelor's degree", "Professional certification"])

    @staticmethod
    def _income_for_age(age: int, occupation: str) -> str:
        occupation_text = occupation.lower()
        if "student" in occupation_text:
            return "INR 0-4 LPA"
        if age > 40 or any(role in occupation_text for role in ("manager", "lead", "director")):
            return random.choice(["INR 18-28 LPA", "INR 25 LPA+"])
        if age < 26:
            return random.choice(["INR 4-8 LPA", "INR 6-10 LPA"])
        return random.choice(["INR 8-14 LPA", "INR 12-18 LPA"])


if __name__ == "__main__":
    generator = PersonaGenerator()
    generated = generator.generate_personas(
        age="25-35",
        gender="Mixed",
        profession="Software Engineer",
        location="India",
        interests="Technology, AI, Shopping",
        persona_count=2,
    )
    print(json.dumps(generated, indent=2))
