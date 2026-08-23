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
    completeness: int
    coherence: int
    realism: int
    behavioral_consistency: int
    research_usefulness: int
    diversity: int
    status: str  # "Valid" or "Needs Review"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PopulationDiversityReport:
    diversity_score: int
    dimension_scores: Dict[str, int]
    warnings: List[str] = field(default_factory=list)
    status: str = "Good Diversity"  # "Good Diversity" or "Low Diversity Detected"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _coerce_num(val: Any, default: float = 0.0) -> float:
    try:
        return float(str(val).replace("%", "").strip())
    except (ValueError, TypeError):
        return default


def _coerce_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, tuple):
        return [str(x).strip() for x in val if str(x).strip()]
    if isinstance(val, Mapping):
        return [f"{k}: {v}" for k, v in val.items() if str(v).strip()]
    return [x.strip() for x in str(val).split(",") if x.strip()]


def _parse_age(val: Any) -> Optional[int]:
    digits = re.findall(r"\d+", str(val or ""))
    return int(digits[0]) if digits else None


def evaluate_persona_quality(
    persona: Mapping[str, Any],
    peers: Optional[Sequence[Mapping[str, Any]]] = None,
) -> PersonaQualityScore:
    """
    Evaluates an individual synthetic persona across 15 heuristic quality checks.
    Produces an auditable Persona Quality Score (0-100) with diagnostic warnings.
    """
    warnings: List[str] = []
    
    # 1. Required fields presence
    missing_fields = [f for f in REQUIRED_FIELDS if persona.get(f) in (None, "", [], {})]
    completeness_pct = (len(REQUIRED_FIELDS) - len(missing_fields)) / len(REQUIRED_FIELDS)
    completeness_score = round(completeness_pct * 100)
    if missing_fields:
        warnings.append(f"Missing required fields: {', '.join(missing_fields[:3])}")

    # 2. Age plausibility check
    age = _parse_age(persona.get("age"))
    age_valid = age is not None and (18 <= age <= 80)
    if not age_valid:
        warnings.append(f"Age '{persona.get('age')}' is out of the supported research range (18-80).")

    # 3 & 4. Occupation and Education plausibility
    occupation = str(persona.get("occupation", "")).strip().lower()
    education = str(persona.get("education", "")).strip().lower()
    coherence_deductions = 0
    if not occupation:
        coherence_deductions += 20
        warnings.append("Occupation is missing or blank.")
    if not education:
        coherence_deductions += 10

    # 5. Income plausibility & consistency with age/role
    income = str(persona.get("income", "")).strip().lower()
    if age and age < 22 and any(term in occupation for term in ("director", "chief", "vp", "senior partner", "head of")):
        coherence_deductions += 25
        warnings.append(f"Senior title '{persona.get('occupation')}' is implausible for age {age}.")
    if "student" in occupation and any(term in income for term in ("25 lpa", "30 lpa", "50 lpa", "$150k", "$200k")):
        coherence_deductions += 20
        warnings.append(f"High income bracket '{persona.get('income')}' is inconsistent with student occupation.")

    # 6 & 7. Goals and Pain points depth
    goals = _coerce_list(persona.get("goals"))
    pain_points = _coerce_list(persona.get("pain_points"))
    realism_deductions = 0
    if len(goals) < 2:
        realism_deductions += 15
        warnings.append("Goals lack sufficient detail (less than 2 items).")
    if len(pain_points) < 2:
        realism_deductions += 15
        warnings.append("Pain points lack sufficient depth (less than 2 items).")

    # 8 & 9. Tech usage and Buying behavior
    tech_usage = str(persona.get("technology_usage", "")).strip().lower()
    buying_behavior = str(persona.get("buying_behavior") or persona.get("buying_behaviour", "")).strip().lower()
    behavior_deductions = 0
    if not tech_usage:
        behavior_deductions += 20
        warnings.append("Technology usage profile is undefined.")
    if not buying_behavior:
        behavior_deductions += 20
        warnings.append("Buying behavior profile is undefined.")

    # 10 & 11. Psychological & Behavioral profile completeness
    psych = persona.get("psychological_profile", {})
    if isinstance(psych, Mapping):
        missing_psych = [k for k in CORE_PSYCH_KEYS if not psych.get(k)]
        if missing_psych:
            behavior_deductions += len(missing_psych) * 4
    else:
        behavior_deductions += 20
        warnings.append("Psychological profile structure is incomplete.")

    behavior = persona.get("behavior_pattern", {})
    if isinstance(behavior, Mapping):
        missing_beh = [k for k in CORE_BEHAVIOR_KEYS if not behavior.get(k)]
        if missing_beh:
            behavior_deductions += len(missing_beh) * 4
    else:
        behavior_deductions += 20
        warnings.append("Behavior pattern structure is incomplete.")

    # 12. Big Five validation
    big_five = persona.get("big_five_personality") or persona.get("big_five") or {}
    if isinstance(big_five, Mapping):
        for trait in BIG_FIVE_KEYS:
            score = _coerce_num(big_five.get(trait))
            if score < 0 or score > 100:
                behavior_deductions += 5
                warnings.append(f"Big Five trait '{trait}' ({score}) must be between 0 and 100.")
    else:
        behavior_deductions += 15
        warnings.append("Big Five personality traits are missing.")

    # 13. Duplicate / peer overlap check
    diversity_score = 85
    if peers:
        same_name = sum(1 for p in peers if str(p.get("name", "")).strip().lower() == str(persona.get("name", "")).strip().lower())
        if same_name > 1:
            warnings.append("Duplicate persona name detected in generated cohort.")
            diversity_score -= 30

    # 14 & 15. Bio realism & internal coherence
    bio = str(persona.get("bio", "")).strip()
    if len(bio) < 70:
        realism_deductions += 20
        warnings.append("Biography is overly brief and lacks research context.")
    elif len(bio) > 120:
        realism_deductions = max(0, realism_deductions - 5)

    if "low" in tech_usage and any(term in buying_behavior for term in ("early adopter", "automation-first", "api-driven")):
        behavior_deductions += 20
        warnings.append("Low tech comfort contradicts early-adopter / automated buying behavior.")

    # Component normalization (0-100)
    coherence_score = max(0, min(100, 100 - coherence_deductions))
    realism_score = max(0, min(100, 100 - realism_deductions))
    behavioral_consistency_score = max(0, min(100, 100 - behavior_deductions))
    
    # Research usefulness: ability to yield distinctive survey/interview signals
    usefulness_score = round((completeness_score * 0.35) + (coherence_score * 0.25) + (realism_score * 0.20) + (behavioral_consistency_score * 0.20))
    
    # Overall weighted score
    overall = round(
        (completeness_score * 0.25)
        + (coherence_score * 0.20)
        + (realism_score * 0.20)
        + (behavioral_consistency_score * 0.20)
        + (diversity_score * 0.15)
    )
    overall_score = max(0, min(100, overall))
    status = "Valid" if overall_score >= QUALITY_THRESHOLD else "Needs Review"

    return PersonaQualityScore(
        overall_score=overall_score,
        completeness=completeness_score,
        coherence=coherence_score,
        realism=realism_score,
        behavioral_consistency=behavioral_consistency_score,
        research_usefulness=usefulness_score,
        diversity=diversity_score,
        status=status,
        warnings=warnings,
    )


def evaluate_population_diversity(personas: Sequence[Mapping[str, Any]]) -> PopulationDiversityReport:
    """
    Evaluates entropy and diversity distribution across a population of generated personas.
    Identifies homogeneous demographic or behavioral clustering.
    """
    if not personas:
        return PopulationDiversityReport(diversity_score=0, dimension_scores={}, warnings=["No personas in cohort."])

    n = len(personas)
    if n == 1:
        return PopulationDiversityReport(
            diversity_score=75,
            dimension_scores={"age": 75, "gender": 75, "occupation": 75, "tech_usage": 75},
            warnings=[],
            status="Good Diversity",
        )

    def _entropy(items: Sequence[str]) -> float:
        counts = Counter(items)
        if len(counts) <= 1:
            return 0.0
        total = len(items)
        h = -sum((c / total) * math.log2(c / total) for c in counts.values())
        max_h = math.log2(min(total, len(counts) if len(counts) > 1 else 2))
        return min(1.0, h / max(0.001, max_h))

    # Age bands
    age_bands = []
    for p in personas:
        a = _parse_age(p.get("age"))
        if not a:
            age_bands.append("unknown")
        elif a < 25:
            age_bands.append("18-24")
        elif a < 35:
            age_bands.append("25-34")
        elif a < 50:
            age_bands.append("35-49")
        else:
            age_bands.append("50+")

    genders = [str(p.get("gender", "")).strip().lower() for p in personas]
    occupations = [str(p.get("occupation", "")).strip().lower() for p in personas]
    tech_usages = [str(p.get("technology_usage", "")).strip().lower() for p in personas]
    buying_styles = [str(p.get("buying_behavior") or p.get("buying_behaviour", "")).strip().lower() for p in personas]

    dim_scores = {
        "age_diversity": round(_entropy(age_bands) * 100),
        "gender_diversity": round(_entropy(genders) * 100),
        "occupation_diversity": round(_entropy(occupations) * 100),
        "tech_adoption_diversity": round(_entropy(tech_usages) * 100),
        "buying_behavior_diversity": round(_entropy(buying_styles) * 100),
    }

    warnings: List[str] = []
    # Detect homogeneity flags
    if n >= 4:
        for dim_name, score in dim_scores.items():
            if score < 25:
                readable = dim_name.replace("_", " ").title()
                warnings.append(f"Low diversity detected in {readable} (Score: {score}/100).")

    avg_diversity = round(sum(dim_scores.values()) / len(dim_scores))
    status = "Good Diversity" if avg_diversity >= 65 else "Low Diversity Detected"

    return PopulationDiversityReport(
        diversity_score=avg_diversity,
        dimension_scores=dim_scores,
        warnings=warnings,
        status=status,
    )
