from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

QUALITY_THRESHOLD = 70

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
]

CORE_PSYCH_KEYS = ["motivation", "values", "decision_style", "risk_tolerance", "emotional_traits"]
CORE_BEHAVIOR_KEYS = ["shopping", "communication", "social_media", "daily_routine", "brand_loyalty"]
BIG_FIVE_KEYS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


@dataclass
class PersonaQualityScore:
    overall_score: int
    realism: int
    coherence: int
    completeness: int
    diversity: int
    behavioral_consistency: int
    research_usefulness: int
    needs_review: bool
    status: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PopulationDiversityReport:
    diversity_score: int
    age_distribution: Dict[str, int] = field(default_factory=dict)
    gender_distribution: Dict[str, int] = field(default_factory=dict)
    occupation_distribution: Dict[str, int] = field(default_factory=dict)
    technology_distribution: Dict[str, int] = field(default_factory=dict)
    buying_behavior_distribution: Dict[str, int] = field(default_factory=dict)
    dimension_scores: Dict[str, int] = field(default_factory=dict)
    is_low_diversity: bool = False
    diversity_warnings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    status: str = "Good Diversity"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _coerce_num(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace("%", "").strip())
    except (TypeError, ValueError):
        return default


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


def _parse_age(value: Any) -> Optional[int]:
    digits = re.findall(r"\d+", str(value or ""))
    return int(digits[0]) if digits else None


def evaluate_peer_diversity(persona: Mapping[str, Any], peers: Sequence[Mapping[str, Any]]) -> int:
    """Calculate diversity score (0-100) for a persona relative to its peer cohort."""
    if not peers or len(peers) <= 1:
        return 85

    other_peers = [
        peer
        for peer in peers
        if peer is not persona and str(peer.get("id", "")) != str(persona.get("id", ""))
    ]
    if not other_peers:
        return 85

    occupation = str(persona.get("occupation", "")).strip().lower()
    gender = str(persona.get("gender", "")).strip().lower()
    tech_usage = str(persona.get("technology_usage", "")).strip().lower()

    occupation_matches = sum(1 for peer in other_peers if str(peer.get("occupation", "")).strip().lower() == occupation)
    gender_matches = sum(1 for peer in other_peers if str(peer.get("gender", "")).strip().lower() == gender)
    tech_matches = sum(1 for peer in other_peers if str(peer.get("technology_usage", "")).strip().lower() == tech_usage)

    duplicate_penalty = (occupation_matches * 15) + (gender_matches * 10) + (tech_matches * 10)
    return max(40, min(100, round(95 - (duplicate_penalty / max(1, len(other_peers))))))


def evaluate_persona_quality(
    persona: Mapping[str, Any],
    peers: Optional[Sequence[Mapping[str, Any]]] = None,
) -> PersonaQualityScore:
    """
    Evaluates an individual synthetic persona across heuristic quality checks.
    Produces an auditable quality score with diagnostic warnings.
    """
    warnings: List[str] = []

    missing_fields = [field_name for field_name in REQUIRED_FIELDS if persona.get(field_name) in (None, "", [], {})]
    completeness_score = round(((len(REQUIRED_FIELDS) - len(missing_fields)) / len(REQUIRED_FIELDS)) * 100)
    if missing_fields:
        warnings.append(f"Missing required fields: {', '.join(missing_fields[:5])}")

    age = _parse_age(persona.get("age"))
    occupation = str(persona.get("occupation", "")).strip().lower()
    education = str(persona.get("education", "")).strip().lower()
    income = str(persona.get("income", "")).strip().lower()
    tech_usage = str(persona.get("technology_usage", "")).strip().lower()
    buying_behavior = str(persona.get("buying_behavior") or persona.get("buying_behaviour", "")).strip().lower()

    coherence_deductions = 0
    realism_deductions = 0
    behavior_deductions = 0

    if age is None or not 18 <= age <= 80:
        realism_deductions += 30
        warnings.append(f"Age '{persona.get('age')}' is outside the supported research range (18-80).")
    if not occupation:
        coherence_deductions += 20
        warnings.append("Occupation is missing or blank.")
    if not education:
        coherence_deductions += 10
    if age and age < 22 and any(term in occupation for term in ("director", "chief", "vp", "senior partner", "head of")):
        coherence_deductions += 25
        warnings.append(f"Senior title '{persona.get('occupation')}' is implausible for age {age}.")
    if "student" in occupation and any(term in income for term in ("25 lpa", "30 lpa", "50 lpa", "$150k", "$200k", "high income")):
        coherence_deductions += 20
        warnings.append(f"Income bracket '{persona.get('income')}' is inconsistent with student occupation.")

    goals = _coerce_list(persona.get("goals"))
    pain_points = _coerce_list(persona.get("pain_points"))
    if len(goals) < 2:
        realism_deductions += 15
        warnings.append("Goals lack sufficient detail.")
    if len(pain_points) < 2:
        realism_deductions += 15
        warnings.append("Pain points lack sufficient depth.")

    if not tech_usage:
        behavior_deductions += 20
        warnings.append("Technology usage profile is undefined.")
    if not buying_behavior:
        behavior_deductions += 20
        warnings.append("Buying behavior profile is undefined.")
    if "low" in tech_usage and any(term in buying_behavior for term in ("early adopter", "automation-first", "automated", "api-driven", "tech-first")):
        behavior_deductions += 20
        warnings.append("Low technology usage conflicts with early-adopter buying behavior.")

    psych = persona.get("psychological_profile", {})
    if isinstance(psych, Mapping):
        behavior_deductions += len([key for key in CORE_PSYCH_KEYS if not psych.get(key)]) * 4
    else:
        behavior_deductions += 20
        warnings.append("Psychological profile structure is incomplete.")

    behavior = persona.get("behavior_pattern", {})
    if isinstance(behavior, Mapping):
        behavior_deductions += len([key for key in CORE_BEHAVIOR_KEYS if not behavior.get(key)]) * 4
    else:
        behavior_deductions += 20
        warnings.append("Behavior pattern structure is incomplete.")

    big_five = persona.get("big_five_personality") or persona.get("big_five") or {}
    if isinstance(big_five, Mapping):
        for trait in BIG_FIVE_KEYS:
            score = _coerce_num(big_five.get(trait))
            if score < 0 or score > 100:
                behavior_deductions += 5
                warnings.append(f"Big Five trait '{trait}' ({score}) must be between 0 and 100.")
        if _coerce_num(big_five.get("openness"), 50) < 20 and "innovative" in str(persona.get("bio", "")).lower():
            coherence_deductions += 15
            warnings.append("Low Big Five openness conflicts with an innovation-oriented bio.")
    else:
        behavior_deductions += 15
        warnings.append("Big Five personality traits are missing.")

    bio = str(persona.get("bio", "")).strip()
    if len(bio) < 70:
        realism_deductions += 20
        warnings.append("Biography is overly brief and lacks research context.")
    elif len(bio) > 120:
        realism_deductions = max(0, realism_deductions - 5)

    diversity_score = evaluate_peer_diversity(persona, peers or [])
    if peers:
        same_name = sum(
            1
            for peer in peers
            if str(peer.get("name", "")).strip().lower() == str(persona.get("name", "")).strip().lower()
        )
        if same_name > 1:
            warnings.append("Duplicate persona name detected in generated cohort.")
            diversity_score = max(40, diversity_score - 30)

    coherence_score = max(0, min(100, 100 - coherence_deductions))
    realism_score = max(0, min(100, 100 - realism_deductions))
    behavioral_consistency_score = max(0, min(100, 100 - behavior_deductions))
    usefulness_score = round(
        (completeness_score * 0.35)
        + (coherence_score * 0.25)
        + (realism_score * 0.20)
        + (behavioral_consistency_score * 0.20)
    )
    overall_score = max(
        0,
        min(
            100,
            round(
                (completeness_score * 0.25)
                + (coherence_score * 0.20)
                + (realism_score * 0.20)
                + (behavioral_consistency_score * 0.20)
                + (diversity_score * 0.15)
            ),
        ),
    )
    needs_review = overall_score < QUALITY_THRESHOLD

    return PersonaQualityScore(
        overall_score=overall_score,
        realism=realism_score,
        coherence=coherence_score,
        completeness=completeness_score,
        diversity=diversity_score,
        behavioral_consistency=behavioral_consistency_score,
        research_usefulness=usefulness_score,
        needs_review=needs_review,
        status="Needs Review" if needs_review else "Valid",
        warnings=warnings,
    )


def _entropy(items: Sequence[str]) -> float:
    counts = Counter(items)
    if len(counts) <= 1:
        return 0.0
    total = len(items)
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    max_entropy = math.log2(min(total, len(counts) if len(counts) > 1 else 2))
    return min(1.0, entropy / max(0.001, max_entropy))


def _age_band(value: Any) -> str:
    age = _parse_age(value)
    if age is None:
        return "Unknown"
    if age < 25:
        return "18-24"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    return "55+"


def evaluate_population_diversity(personas: Sequence[Mapping[str, Any]]) -> PopulationDiversityReport:
    """
    Evaluates entropy and distribution diversity across a generated persona cohort.
    """
    if not personas:
        warning = "No personas in cohort."
        return PopulationDiversityReport(
            diversity_score=0,
            is_low_diversity=True,
            diversity_warnings=[warning],
            warnings=[warning],
            status="Low Diversity Detected",
        )

    age_bands = [_age_band(persona.get("age")) for persona in personas]
    genders = [str(persona.get("gender", "Mixed")).strip().title() for persona in personas]
    occupations = [str(persona.get("occupation", "Professional")).strip().title() for persona in personas]
    tech_usages = [str(persona.get("technology_usage", "Medium")).strip().title() for persona in personas]
    buying_styles = [
        str(persona.get("buying_behavior") or persona.get("buying_behaviour", "Value-seeking")).strip().title()[:40]
        for persona in personas
    ]

    age_distribution = dict(Counter(age_bands))
    gender_distribution = dict(Counter(genders))
    occupation_distribution = dict(Counter(occupations))
    technology_distribution = dict(Counter(tech_usages))
    buying_behavior_distribution = dict(Counter(buying_styles))

    dimension_scores = {
        "age_diversity": round(_entropy(age_bands) * 100),
        "gender_diversity": round(_entropy(genders) * 100),
        "occupation_diversity": round(_entropy(occupations) * 100),
        "tech_adoption_diversity": round(_entropy(tech_usages) * 100),
        "buying_behavior_diversity": round(_entropy(buying_styles) * 100),
    }

    if len(personas) == 1:
        diversity_score = 75
    else:
        diversity_score = round(sum(dimension_scores.values()) / max(1, len(dimension_scores)))

    warnings: List[str] = []
    total = len(personas)
    if total >= 4:
        for dimension, score in dimension_scores.items():
            if score < 25:
                warnings.append(f"Low diversity detected in {dimension.replace('_', ' ')} ({score}/100).")

        max_occupation_ratio = max(occupation_distribution.values()) / total
        if max_occupation_ratio >= 0.70:
            warnings.append(f"Low persona diversity detected: {round(max_occupation_ratio * 100)}% share the same occupation.")

        max_tech_ratio = max(technology_distribution.values()) / total
        if max_tech_ratio >= 0.75:
            warnings.append(f"Low technology diversity detected: {round(max_tech_ratio * 100)}% share the same tech adoption tier.")

    is_low_diversity = diversity_score < 65
    status = "Low Diversity Detected" if is_low_diversity else "Good Diversity"

    return PopulationDiversityReport(
        diversity_score=max(0, min(100, diversity_score)),
        age_distribution=age_distribution,
        gender_distribution=gender_distribution,
        occupation_distribution=occupation_distribution,
        technology_distribution=technology_distribution,
        buying_behavior_distribution=buying_behavior_distribution,
        dimension_scores=dimension_scores,
        is_low_diversity=is_low_diversity,
        diversity_warnings=warnings,
        warnings=warnings,
        status=status,
    )
