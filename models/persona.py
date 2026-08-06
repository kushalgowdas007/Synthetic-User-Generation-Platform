from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional


def _coerce_text(value: Any, default: str = "Not provided") -> str:
    """Convert arbitrary values into a readable string with a safe fallback."""
    if value is None:
        return default

    if isinstance(value, str):
        text = value.strip()
        return text or default

    if isinstance(value, (int, float)):
        return str(value)

    text = str(value).strip()
    return text or default


def _coerce_list(value: Any) -> List[str]:
    """Normalize list-like values into a clean list of strings."""
    if value is None:
        return []

    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, str):
        items = [item.strip() for item in value.split(",") if item.strip()]
    elif isinstance(value, dict):
        items = [f"{key}: {item}" for key, item in value.items() if item not in (None, "")]
    else:
        items = [str(value)]

    cleaned_items: List[str] = []
    for item in items:
        text = str(item).strip() if not isinstance(item, str) else item.strip()
        if text:
            cleaned_items.append(text)

    return cleaned_items


def _coerce_score(value: Any, default: float = 0.0) -> float:
    """Safely convert Big Five score input to a float."""
    if value in (None, ""):
        return default

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("%", "")
    try:
        return float(text)
    except ValueError:
        return default


def _coerce_timestamp(value: Any, default: str = "") -> str:
    """Normalize created/updated timestamps into a string."""
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return str(value)

    return str(value).strip() or default


@dataclass
class BigFivePersonality:
    """Structured Big Five personality profile with safe defaults."""

    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0

    @classmethod
    def from_value(cls, value: Any) -> "BigFivePersonality":
        if isinstance(value, cls):
            return value

        if isinstance(value, Mapping):
            return cls(
                openness=_coerce_score(value.get("openness")),
                conscientiousness=_coerce_score(value.get("conscientiousness")),
                extraversion=_coerce_score(value.get("extraversion")),
                agreeableness=_coerce_score(value.get("agreeableness")),
                neuroticism=_coerce_score(value.get("neuroticism")),
            )

        if isinstance(value, (list, tuple)) and len(value) >= 5:
            return cls(
                openness=_coerce_score(value[0]),
                conscientiousness=_coerce_score(value[1]),
                extraversion=_coerce_score(value[2]),
                agreeableness=_coerce_score(value[3]),
                neuroticism=_coerce_score(value[4]),
            )

        return cls()

    def to_dict(self) -> Mapping[str, float]:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }


@dataclass
class Persona:
    """Flexible persona data model that supports legacy and milestone-2 schema."""

    name: str = "Unknown"
    age: str = "N/A"
    gender: str = "Not provided"
    occupation: str = "Not provided"
    education: str = "Not provided"
    income: str = "Not provided"
    email: str = "Not provided"
    phone: str = "Not provided"
    address: str = "Not provided"
    city: str = "Not provided"
    state: str = "Not provided"
    pincode: str = "Not provided"
    id: str = ""
    avatar_url: str = ""
    company: str = "Not provided"
    goals: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    behaviour: List[str] = field(default_factory=list)
    technology_usage: str = "Not provided"
    buying_behaviour: str = "Not provided"
    psychological_profile: Any = "Not provided"
    behavior_pattern: Any = "Not provided"
    created_at: str = ""
    updated_at: str = ""
    big_five: BigFivePersonality = field(default_factory=BigFivePersonality)

    @classmethod
    def from_dict(cls, data: Optional[Mapping[str, Any]]) -> "Persona":
        payload = dict(data or {})

        big_five_payload = (
            payload.get("big_five")
            or payload.get("big_five_personality")
            or payload.get("big_five_personality_scores")
            or payload.get("big_five_scores")
            or {}
        )

        if not big_five_payload and any(
            key in payload for key in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")
        ):
            big_five_payload = {
                "openness": payload.get("openness"),
                "conscientiousness": payload.get("conscientiousness"),
                "extraversion": payload.get("extraversion"),
                "agreeableness": payload.get("agreeableness"),
                "neuroticism": payload.get("neuroticism"),
            }

        return cls(
            id=_coerce_text(
                payload.get("id")
                or payload.get("persona_id")
                or payload.get("uuid")
                or payload.get("uid"),
                "",
            ),
            avatar_url=_coerce_text(
                payload.get("avatar_url")
                or payload.get("avatar")
                or payload.get("image_url")
                or payload.get("photo_url"),
                "",
            ),
            name=_coerce_text(payload.get("name"), "Unknown"),
            age=_coerce_text(payload.get("age"), "N/A"),
            gender=_coerce_text(payload.get("gender"), "Not provided"),
            occupation=_coerce_text(payload.get("occupation"), "Not provided"),
            education=_coerce_text(payload.get("education"), "Not provided"),
            income=_coerce_text(payload.get("income"), "Not provided"),
            email=_coerce_text(payload.get("email"), "Not provided"),
            phone=_coerce_text(payload.get("phone"), "Not provided"),
            address=_coerce_text(payload.get("address"), "Not provided"),
            city=_coerce_text(payload.get("city"), "Not provided"),
            state=_coerce_text(payload.get("state"), "Not provided"),
            pincode=_coerce_text(payload.get("pincode") or payload.get("postcode"), "Not provided"),
            company=_coerce_text(payload.get("company"), "Not provided"),
            goals=_coerce_list(payload.get("goals")),
            pain_points=_coerce_list(payload.get("pain_points")),
            traits=_coerce_list(payload.get("traits")),
            behaviour=_coerce_list(payload.get("behaviour") or payload.get("behavior") or payload.get("behaviors")),
            technology_usage=_coerce_text(
                payload.get("technology_usage") or payload.get("technology") or payload.get("tech_usage"),
                "Not provided",
            ),
            buying_behaviour=_coerce_text(
                payload.get("buying_behaviour") or payload.get("buying_behavior"),
                "Not provided",
            ),
            psychological_profile=payload.get("psychological_profile") or payload.get("psychology") or payload.get("psychological"),
            behavior_pattern=payload.get("behavior_pattern") or payload.get("behaviour_pattern") or payload.get("behavior"),
            created_at=_coerce_timestamp(
                payload.get("created_at") or payload.get("createdAt") or payload.get("created"),
                "",
            ),
            updated_at=_coerce_timestamp(
                payload.get("updated_at") or payload.get("updatedAt") or payload.get("updated"),
                "",
            ),
            big_five=BigFivePersonality.from_value(big_five_payload),
        )

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "id": self.id,
            "avatar_url": self.avatar_url,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation,
            "education": self.education,
            "income": self.income,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "company": self.company,
            "goals": list(self.goals),
            "pain_points": list(self.pain_points),
            "traits": list(self.traits),
            "behaviour": list(self.behaviour),
            "technology_usage": self.technology_usage,
            "buying_behaviour": self.buying_behaviour,
            "psychological_profile": self.psychological_profile,
            "behavior_pattern": self.behavior_pattern,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "big_five": self.big_five.to_dict(),
        }
