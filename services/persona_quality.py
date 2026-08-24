from __future__ import annotations

<<<<<<< HEAD
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
=======
import re
from collections import Counter
from typing import Any, Dict, List, Mapping, Optional, Sequence
from models.schemas import PersonaQualityScore, PopulationDiversityReport


QUALITY_THRESHOLD = 70


def evaluate_persona_quality(persona: Mapping[str, Any], peers: Optional[Sequence[Mapping[str, Any]]] = None) -> PersonaQualityScore:
    """
    Evaluate an individual persona across 6 dimensions and return a PersonaQualityScore.
    """
    warnings: List[str] = []
    
    # 1. Completeness Check
    required_fields = [
        "name", "age", "gender", "occupation", "education", "income", "bio",
        "goals", "pain_points", "technology_usage", "buying_behavior",
        "psychological_profile", "behavior_pattern", "big_five_personality"
    ]
    present_count = sum(1 for field in required_fields if persona.get(field) not in (None, "", [], {}))
    completeness = round((present_count / len(required_fields)) * 100)
    if completeness < 100:
        missing = [f for f in required_fields if persona.get(f) in (None, "", [], {})]
        warnings.append(f"Missing required fields: {', '.join(missing)}")

    # 2. Realism Check
    realism = 90
    age_raw = persona.get("age")
    try:
        age = int(re.findall(r"\d+", str(age_raw))[0]) if age_raw is not None else 30
    except (IndexError, ValueError):
        age = 30
        
    if age < 18 or age > 80:
        realism -= 30
        warnings.append(f"Age {age} is outside plausible research range (18-80).")

    bio = str(persona.get("bio", ""))
    if len(bio) < 60:
        realism -= 20
        warnings.append("Bio is too brief for a realistic research persona.")
        
    occupation = str(persona.get("occupation", "")).lower()
    income = str(persona.get("income", "")).lower()
    education = str(persona.get("education", "")).lower()

    if "student" in occupation and any(high in income for high in ["25 lpa", "30 lpa", "$150", "high income"]):
        realism -= 25
        warnings.append("⚠ Income and occupation may be inconsistent for student persona.")
        
    if age < 22 and any(senior in occupation for senior in ["senior", "director", "vp", "chief", "head of"]):
        realism -= 25
        warnings.append("⚠ Age and senior job title appear inconsistent.")
        
    realism = max(0, min(100, realism))

    # 3. Coherence Check
    coherence = 92
    tech_usage = str(persona.get("technology_usage", "")).lower()
    buying = str(persona.get("buying_behavior", "") or persona.get("buying_behaviour", "")).lower()
    
    if "low" in tech_usage and any(term in buying for term in ["early adopter", "automated", "tech-first"]):
        coherence -= 20
        warnings.append("⚠ Low technology usage conflicts with early adopter buying behavior.")

    big_five = persona.get("big_five_personality", {})
    if isinstance(big_five, Mapping):
        openness = float(big_five.get("openness", 50))
        if openness < 20 and "innovative" in bio.lower():
            coherence -= 15
            warnings.append("⚠ Big Five Openness score is low despite innovative bio description.")

    coherence = max(0, min(100, coherence))

    # 4. Behavioral Consistency Check
    goals = persona.get("goals", [])
    pain_points = persona.get("pain_points", [])
    behavioral_consistency = 90
    
    if not isinstance(goals, list) or len(goals) < 2:
        behavioral_consistency -= 15
        warnings.append("⚠ Persona goals lack sufficient detail.")
    if not isinstance(pain_points, list) or len(pain_points) < 2:
        behavioral_consistency -= 15
        warnings.append("⚠ Persona pain points lack sufficient detail.")

    behavioral_consistency = max(0, min(100, behavioral_consistency))

    # 5. Research Usefulness Check
    usefulness = 95
    if len(str(persona.get("name", ""))) < 2:
        usefulness -= 30
    if not persona.get("psychological_profile"):
        usefulness -= 20
    usefulness = max(0, min(100, usefulness))

    # 6. Diversity Score relative to peers
    diversity = evaluate_peer_diversity(persona, peers or [])

    # Composite overall score
    overall = round(
        (completeness * 0.20) +
        (realism * 0.20) +
        (coherence * 0.20) +
        (behavioral_consistency * 0.15) +
        (usefulness * 0.15) +
        (diversity * 0.10)
    )
    overall = max(0, min(100, overall))

    needs_review = overall < QUALITY_THRESHOLD

    return PersonaQualityScore(
        overall_score=overall,
        realism=realism,
        coherence=coherence,
        completeness=completeness,
        diversity=diversity,
        behavioral_consistency=behavioral_consistency,
        research_usefulness=usefulness,
        needs_review=needs_review,
>>>>>>> f68520b (Save local changes)
        warnings=warnings,
    )


<<<<<<< HEAD
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
=======
def evaluate_peer_diversity(persona: Mapping[str, Any], peers: Sequence[Mapping[str, Any]]) -> int:
    """Calculate diversity score (0-100) for a persona relative to its peer cohort."""
    if not peers or len(peers) <= 1:
        return 85

    other_peers = [p for p in peers if p is not persona and str(p.get("id")) != str(persona.get("id"))]
    if not other_peers:
        return 85

    my_occ = str(persona.get("occupation", "")).strip().lower()
    my_gender = str(persona.get("gender", "")).strip().lower()
    my_tech = str(persona.get("technology_usage", "")).strip().lower()
    
    occ_matches = sum(1 for p in other_peers if str(p.get("occupation", "")).strip().lower() == my_occ)
    gender_matches = sum(1 for p in other_peers if str(p.get("gender", "")).strip().lower() == my_gender)
    tech_matches = sum(1 for p in other_peers if str(p.get("technology_usage", "")).strip().lower() == my_tech)
    
    dup_penalty = (occ_matches * 15) + (gender_matches * 10) + (tech_matches * 10)
    return max(40, min(100, round(95 - (dup_penalty / max(1, len(other_peers))))))


def evaluate_population_diversity(personas: Sequence[Mapping[str, Any]]) -> PopulationDiversityReport:
    """
    Evaluate overall diversity across a population of generated personas.
    """
    if not personas:
        return PopulationDiversityReport(diversity_score=0, is_low_diversity=True, diversity_warnings=["No personas to evaluate."])

    total = len(personas)
    age_dist: Dict[str, int] = {}
    gender_dist: Dict[str, int] = {}
    occ_dist: Dict[str, int] = {}
    tech_dist: Dict[str, int] = {}
    buying_dist: Dict[str, int] = {}
    
    warnings: List[str] = []

    for p in personas:
        # Age band
        age_val = p.get("age", 30)
        try:
            age = int(re.findall(r"\d+", str(age_val))[0])
        except Exception:
            age = 30
        band = "18-24" if age < 25 else "25-34" if age < 35 else "35-44" if age < 45 else "45-54" if age < 55 else "55+"
        age_dist[band] = age_dist.get(band, 0) + 1
        
        # Gender
        g = str(p.get("gender", "Mixed")).title()
        gender_dist[g] = gender_dist.get(g, 0) + 1
        
        # Occupation
        occ = str(p.get("occupation", "Professional")).title()
        occ_dist[occ] = occ_dist.get(occ, 0) + 1

        # Tech
        tech = str(p.get("technology_usage", "Medium")).title()
        tech_dist[tech] = tech_dist.get(tech, 0) + 1

        # Buying
        b = str(p.get("buying_behavior", "Value-seeking")).title()[:25]
        buying_dist[b] = buying_dist.get(b, 0) + 1

    # Check for excessive homogeneity (e.g. >70% identical in key attribute if N>=4)
    diversity_score = 90
    
    if total >= 4:
        max_occ_ratio = max(occ_dist.values()) / total
        if max_occ_ratio >= 0.7:
            diversity_score -= 25
            warnings.append(f"Low persona diversity detected: {round(max_occ_ratio*100)}% of personas share the same occupation.")
            
        max_tech_ratio = max(tech_dist.values()) / total
        if max_tech_ratio >= 0.75:
            diversity_score -= 20
            warnings.append(f"Low technology diversity detected: {round(max_tech_ratio*100)}% share the same tech adoption tier.")

        max_gender_ratio = max(gender_dist.values()) / total
        if max_gender_ratio == 1.0 and total >= 3:
            diversity_score -= 15
            warnings.append("Gender population lacks variation across persona cards.")

    is_low = diversity_score < 70

    return PopulationDiversityReport(
        diversity_score=max(0, min(100, diversity_score)),
        age_distribution=age_dist,
        gender_distribution=gender_dist,
        occupation_distribution=occ_dist,
        technology_distribution=tech_dist,
        buying_behavior_distribution=buying_dist,
        is_low_diversity=is_low,
        diversity_warnings=warnings,
>>>>>>> f68520b (Save local changes)
    )
