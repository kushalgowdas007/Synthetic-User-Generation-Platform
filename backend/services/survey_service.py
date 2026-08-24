from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence


# ============================================================
# SURVEY QUESTIONS / TEMPLATES
# ============================================================

DEFAULT_SURVEY_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q1",
        "question": "How important is a smooth onboarding experience for the product?",
        "category": "Onboarding",
        "type": "single_choice",
        "options": [
            "Not important",
            "Somewhat important",
            "Important",
            "Very important",
        ],
        "weight": 1,
    },
    {
        "id": "q2",
        "question": "How likely are you to adopt a solution that reduces your current pain points?",
        "category": "Adoption",
        "type": "single_choice",
        "options": [
            "Very unlikely",
            "Unlikely",
            "Possible",
            "Very likely",
        ],
        "weight": 1,
    },
    {
        "id": "q3",
        "question": "How likely are you to recommend this product to peers after trying it?",
        "category": "Recommendation",
        "type": "single_choice",
        "options": [
            "No",
            "Maybe",
            "Likely",
            "Highly likely",
        ],
        "weight": 1,
    },
]

class _CaseInsensitiveTemplatesDict(dict):
    def __getitem__(self, key: str) -> Any:
        if key in self:
            return super().__getitem__(key)
        key_lower = str(key).lower()
        for k in self:
            if str(k).lower() == key_lower:
                return super().__getitem__(k)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

SURVEY_TEMPLATES: Dict[str, List[Dict[str, Any]]] = _CaseInsensitiveTemplatesDict({
    "Product Adoption": DEFAULT_SURVEY_QUESTIONS,
    "Pricing and Value": [
        {
            "id": "price_1",
            "question": "How fair does the expected price feel for the value this product provides?",
            "category": "Pricing",
            "type": "single_choice",
            "options": ["Not fair", "Somewhat fair", "Fair", "Very fair"],
            "weight": 1,
        },
        {
            "id": "price_2",
            "question": "Would a free trial reduce your hesitation to try this product?",
            "category": "Trial",
            "type": "single_choice",
            "options": ["Not at all", "A little", "Mostly", "Definitely"],
            "weight": 1,
        },
        {
            "id": "price_3",
            "question": "How much proof of value would you need before paying?",
            "category": "Trust",
            "type": "single_choice",
            "options": ["Very little", "Some proof", "Strong proof", "Detailed proof"],
            "weight": 1,
        },
    ],
    "Usability and Trust": [
        {
            "id": "trust_1",
            "question": "How important are trust signals and transparent information before adoption?",
            "category": "Trust",
            "type": "single_choice",
            "options": [
                "Not important",
                "Somewhat important",
                "Important",
                "Very important",
            ],
            "weight": 1,
        },
        {
            "id": "trust_2",
            "question": "How confident would you feel completing the first task without help?",
            "category": "Usability",
            "type": "single_choice",
            "options": [
                "Not confident",
                "Somewhat confident",
                "Confident",
                "Very confident",
            ],
            "weight": 1,
        },
        {
            "id": "trust_3",
            "question": "Would unclear navigation stop you from using this product regularly?",
            "category": "Barriers",
            "type": "single_choice",
            "options": [
                "Definitely",
                "Probably",
                "Not much",
                "Not at all",
            ],
            "weight": 1,
        },
    ],
    "Retention and Loyalty": [
        {
            "id": "retention_1",
            "question": "How likely are you to keep using this product after the first month?",
            "category": "Retention",
            "type": "single_choice",
            "options": ["Unlikely", "Maybe", "Likely", "Very likely"],
            "weight": 1,
        },
        {
            "id": "retention_2",
            "question": "Which factor would most influence repeat usage?",
            "category": "Behavior",
            "type": "single_choice",
            "options": [
                "Price",
                "Ease of use",
                "Outcome quality",
                "Habit formation",
            ],
            "weight": 1,
        },
        {
            "id": "retention_3",
            "question": "Would reminders or progress tracking help you stay engaged?",
            "category": "Engagement",
            "type": "single_choice",
            "options": ["No", "Maybe", "Likely", "Definitely"],
            "weight": 1,
        },
    ],
    "Feature Discovery": [
        {
            "id": "feature_1",
            "question": "Which feature type would create the strongest first impression?",
            "category": "Feature Request",
            "type": "single_choice",
            "options": [
                "Automation",
                "Analytics",
                "Personalization",
                "Collaboration",
            ],
            "weight": 1,
        },
        {
            "id": "feature_2",
            "question": "How important is personalization to your adoption decision?",
            "category": "Personalization",
            "type": "single_choice",
            "options": [
                "Not important",
                "Somewhat important",
                "Important",
                "Very important",
            ],
            "weight": 1,
        },
        {
            "id": "feature_3",
            "question": "Would integrations with current tools increase product fit?",
            "category": "Integration",
            "type": "single_choice",
            "options": ["No", "Maybe", "Likely", "Definitely"],
            "weight": 1,
        },
    ],
})

# Backward-compatible aliases for older code/templates.
SURVEY_TEMPLATES["Product adoption"] = SURVEY_TEMPLATES["Product Adoption"]
SURVEY_TEMPLATES["Pricing Sensitivity"] = SURVEY_TEMPLATES["Pricing and Value"]
SURVEY_TEMPLATES["Usability and onboarding"] = SURVEY_TEMPLATES["Usability and Trust"]


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def _normalize_persona(persona: Any) -> Dict[str, Any]:
    if isinstance(persona, Mapping):
        return dict(persona)

    if hasattr(persona, "to_dict"):
        try:
            return dict(persona.to_dict())
        except Exception:
            pass

    if hasattr(persona, "model_dump"):
        try:
            return dict(persona.model_dump())
        except Exception:
            pass

    return {}


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    return [str(value).strip()]


def _coerce_text(
    value: Any,
    default: str = "Not provided",
) -> str:
    if value is None:
        return default

    text = str(value).strip()
    return text or default


def _coerce_score(
    value: Any,
    default: float = 0.0,
) -> float:
    if value in (None, ""):
        return default

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace("%", "")

    try:
        return float(text)
    except (ValueError, TypeError):
        return default


def _safe_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        2,
    )


def _word_tokens(value: Any) -> List[str]:
    text = str(value or "")

    return [
        token.lower()
        for token in re.findall(
            r"[a-zA-Z]+",
            text,
        )
        if len(token) > 2
    ]


def _overlap_score(
    text: str,
    keywords: Sequence[str],
) -> float:
    source_tokens = set(
        _word_tokens(text)
    )

    target_tokens = {
        token.lower()
        for token in keywords
        if token
    }

    if not target_tokens:
        return 0.0

    overlap = len(
        source_tokens.intersection(
            target_tokens
        )
    )

    return min(
        100.0,
        round(
            (
                overlap
                / max(len(target_tokens), 1)
            )
            * 100.0,
            2,
        ),
    )


def _strongest_summary(
    summary_map: Mapping[str, float],
) -> str:
    if not summary_map:
        return "No dominant pattern yet."

    strongest = max(
        summary_map.items(),
        key=lambda item: item[1],
    )

    return (
        f"{strongest[0]} is the strongest "
        "observed signal."
    )


# ============================================================
# QUESTION BUILDING
# ============================================================

def _normalize_question(
    question: Any,
    index: int,
    product_name: str,
    research_goal: str,
) -> Dict[str, Any]:
    if isinstance(question, Mapping):
        source = dict(question)

        text = _coerce_text(
            source.get("question")
            or source.get("text"),
            "How helpful is this product?",
        )

        options = source.get("options") or [
            "Very unlikely",
            "Unlikely",
            "Likely",
            "Very likely",
        ]

        question_type = _coerce_text(
            source.get("type"),
            "single_choice",
        )

        category = _coerce_text(
            source.get("category"),
            "General",
        )

        weight = int(
            _coerce_score(
                source.get("weight"),
                1,
            )
            or 1
        )

        question_id = _coerce_text(
            source.get("id"),
            f"q{index + 1}",
        )

    else:
        text = _coerce_text(
            question,
            "How helpful is this product?",
        )
        options = [
            "Very unlikely",
            "Unlikely",
            "Likely",
            "Very likely",
        ]
        question_type = "single_choice"
        category = "Custom"
        weight = 1
        question_id = f"custom_{index + 1}"

    normalized_options = (
        list(options)
        if isinstance(
            options,
            (list, tuple),
        )
        else _coerce_list(options)
    )

    if not normalized_options:
        normalized_options = [
            "Very unlikely",
            "Unlikely",
            "Likely",
            "Very likely",
        ]

    return {
        "id": question_id,
        "question": text,
        "category": category,
        "type": question_type,
        "options": normalized_options,
        "weight": max(1, weight),
        "product_name": str(
            product_name or ""
        ),
        "research_goal": str(
            research_goal or ""
        ),
    }


def _dynamic_questions(
    product_name: str,
    research_goal: str,
) -> List[Dict[str, Any]]:
    product_label = (
        product_name.strip()
        or "this product"
    )

    goal_label = (
        research_goal.strip()
        or "your main goal"
    )

    return [
        {
            "id": "dyn_goal_fit",
            "question": (
                f"How well does {product_label} "
                f"support {goal_label}?"
            ),
            "category": "Product Fit",
            "type": "single_choice",
            "options": [
                "Poorly",
                "Somewhat",
                "Well",
                "Very well",
            ],
            "weight": 2,
        },
        {
            "id": "dyn_barrier",
            "question": (
                f"What would most prevent you "
                f"from adopting {product_label}?"
            ),
            "category": "Barriers",
            "type": "single_choice",
            "options": [
                "Price",
                "Trust",
                "Learning curve",
                "Low need",
            ],
            "weight": 2,
        },
    ]


def create_survey(
    product_name: str = "",
    research_goal: str = "",
    survey_questions: Optional[
        Sequence[Any]
    ] = None,
    template_name: str = "Product Adoption",
    include_dynamic_questions: bool = False,
) -> List[Dict[str, Any]]:
    """Create a normalized survey question list."""

    template_questions = SURVEY_TEMPLATES.get(
        template_name,
        DEFAULT_SURVEY_QUESTIONS,
    )

    if survey_questions is None:
        questions = list(
            template_questions
        )
    else:
        questions = list(
            survey_questions
        )

    if include_dynamic_questions:
        questions.extend(
            _dynamic_questions(
                product_name,
                research_goal,
            )
        )

    valid_questions = []

    for question in questions:
        if isinstance(question, Mapping):
            if not str(
                question.get("question", "")
            ).strip():
                continue

        elif not str(question).strip():
            continue

        valid_questions.append(question)

    if not valid_questions:
        valid_questions = list(
            DEFAULT_SURVEY_QUESTIONS
        )

    return [
        _normalize_question(
            question,
            index,
            product_name,
            research_goal,
        )
        for index, question in enumerate(
            valid_questions
        )
    ]


# ============================================================
# PERSONA PRODUCT-FIT MODEL
# ============================================================

def _build_weighted_product_fit(
    persona: Mapping[str, Any],
    product_name: str,
    research_goal: str,
) -> Dict[str, Any]:

    goals = " ".join(
        _coerce_list(
            persona.get("goals")
        )
    )

    pain_points = " ".join(
        _coerce_list(
            persona.get("pain_points")
        )
    )

    behaviour = " ".join(
        _coerce_list(
            persona.get("behaviour")
            or persona.get("behavior")
            or persona.get("behavior_pattern")
        )
    )

    tech_usage = _coerce_text(
        persona.get(
            "technology_usage"
        )
    )

    buying_behaviour = _coerce_text(
        persona.get("buying_behaviour")
        or persona.get("buying_behavior")
    )

    occupation = _coerce_text(
        persona.get("occupation")
    )

    big_five = (
        persona.get("big_five")
        or persona.get(
            "big_five_personality"
        )
        or {}
    )

    if isinstance(
        big_five,
        Mapping,
    ):
        openness = _coerce_score(
            big_five.get("openness")
        )
        conscientiousness = _coerce_score(
            big_five.get("conscientiousness")
        )
        extraversion = _coerce_score(
            big_five.get("extraversion")
        )
        agreeableness = _coerce_score(
            big_five.get("agreeableness")
        )
        neuroticism = _coerce_score(
            big_five.get("neuroticism")
        )
    else:
        openness = 0.0
        conscientiousness = 0.0
        extraversion = 0.0
        agreeableness = 0.0
        neuroticism = 0.0

    product_context = (
        f"{product_name} {research_goal}"
    ).lower()

    pain_point_keywords = [
        "value",
        "affordability",
        "price",
        "budget",
        "cost",
        "time",
        "ease",
        "friction",
        "complexity",
        "stress",
        "motivation",
        "convenience",
        "trust",
        "integration",
        "speed",
        "learning",
    ]

    goal_keywords = [
        "career",
        "success",
        "growth",
        "health",
        "wellness",
        "efficiency",
        "learning",
        "retention",
        "productivity",
        "automation",
        "mobility",
        "insight",
    ]

    tech_keywords = [
        "mobile",
        "desktop",
        "ai",
        "automation",
        "cloud",
        "analytics",
        "app",
        "wearable",
        "technology",
    ]

    buying_keywords = [
        "affordability",
        "value",
        "quality",
        "convenience",
        "easy",
        "trust",
        "speed",
    ]

    industry_keywords = [
        "health",
        "finance",
        "education",
        "retail",
        "technology",
        "travel",
        "media",
    ]

    pain_point_match = _overlap_score(
        f"{pain_points} {product_context}",
        pain_point_keywords,
    )

    goal_match = _overlap_score(
        f"{goals} {product_context}",
        goal_keywords,
    )

    technology_match = _overlap_score(
        f"{tech_usage} {product_context}",
        tech_keywords,
    )

    buying_behaviour_score = _overlap_score(
        (
            f"{buying_behaviour} "
            f"{behaviour} "
            f"{product_context}"
        ),
        buying_keywords,
    )

    psychological_alignment = min(
        100.0,
        round(
            (
                (
                    openness
                    + conscientiousness
                    + extraversion
                    + agreeableness
                )
                / 4.0
            )
            * 0.8
            + (100 - neuroticism) * 0.2,
            2,
        ),
    )

    industry_alignment = _overlap_score(
        f"{occupation} {product_context}",
        industry_keywords,
    )

    weights = {
        "Pain Point Match": 0.18,
        "Goal Match": 0.18,
        "Technology Match": 0.15,
        "Buying Behaviour": 0.14,
        "Psychological Alignment": 0.17,
        "Industry Alignment": 0.18,
    }

    category_scores = {
        "Pain Point Match": round(
            pain_point_match,
            2,
        ),
        "Goal Match": round(
            goal_match,
            2,
        ),
        "Technology Match": round(
            technology_match,
            2,
        ),
        "Buying Behaviour": round(
            buying_behaviour_score,
            2,
        ),
        "Psychological Alignment": round(
            psychological_alignment,
            2,
        ),
        "Industry Alignment": round(
            industry_alignment,
            2,
        ),
    }

    overall_compatibility = round(
        sum(
            category_scores[key]
            * weights[key]
            for key in category_scores
        ),
        2,
    )

    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []

    for key, score in category_scores.items():
        if score >= 70:
            strengths.append(key)
        elif score < 45:
            weaknesses.append(key)

    if not weaknesses:
        weaknesses.append(
            "No major risk flags detected"
        )

    if any(
        item in strengths
        for item in (
            "Goal Match",
            "Pain Point Match",
        )
    ):
        recommendations.append(
            "Position the product around high-value, "
            "low-friction outcomes that directly address "
            "the persona's stated goals."
        )

    if "Technology Match" in strengths:
        recommendations.append(
            "Keep the mobile-first and automation-first "
            "experience as a central selling message."
        )

    if "Buying Behaviour" in weaknesses:
        recommendations.append(
            "Reinforce affordability and clarity in "
            "messaging to improve conversion intent."
        )

    if "Psychological Alignment" in weaknesses:
        recommendations.append(
            "Use onboarding nudges and trust-building "
            "content to reduce hesitation."
        )

    return {
        "overall_score": round(
            overall_compatibility,
            2,
        ),
        "category_scores": category_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "summary": _strongest_summary(
            category_scores
        ),
    }


# ============================================================
# RESPONSE SIMULATION
# ============================================================

def _answer_for_score(
    score: int,
    options: Sequence[str],
) -> str:
    if not options:
        return "No response"

    if score >= 85:
        return options[-1]

    if score >= 65:
        return (
            options[-2]
            if len(options) > 1
            else options[-1]
        )

    if score >= 45:
        return (
            options[-3]
            if len(options) > 2
            else options[0]
        )

    return options[0]


def _confidence_for_score(
    score: int,
) -> int:
    return max(
        60,
        min(98, int(score)),
    )


def _emotion_for_score(
    score: int,
) -> str:
    if score >= 80:
        return "excited"

    if score >= 60:
        return "positive"

    if score >= 40:
        return "neutral"

    return "cautious"


def execute_survey(
    personas: Any,
    product_name: str = "",
    research_goal: str = "",
    survey_questions: Optional[
        Sequence[Any]
    ] = None,
    template_name: str = "Product Adoption",
    include_dynamic_questions: bool = False,
) -> Dict[str, Any]:
    """
    Execute a deterministic, persona-consistent synthetic survey.

    No external API is required for this workflow.
    """

    if personas is None:
        normalized_personas: List[
            Dict[str, Any]
        ] = []

    elif isinstance(
        personas,
        Mapping,
    ):
        normalized_personas = [
            _normalize_persona(personas)
        ]

    elif isinstance(
        personas,
        list,
    ):
        normalized_personas = [
            _normalize_persona(persona)
            for persona in personas
            if persona is not None
        ]

    else:
        normalized_personas = [
            _normalize_persona(personas)
        ]

    questions = create_survey(
        product_name=product_name,
        research_goal=research_goal,
        survey_questions=survey_questions,
        template_name=template_name,
        include_dynamic_questions=(
            include_dynamic_questions
        ),
    )

    responses: List[
        Dict[str, Any]
    ] = []

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    for index, persona in enumerate(
        normalized_personas
    ):

        persona_name = _coerce_text(
            persona.get("name"),
            f"Persona {index + 1}",
        )

        persona_id = _coerce_text(
            persona.get("id"),
            f"persona-{index + 1}",
        )

        persona_age = _coerce_text(
            persona.get("age"),
            "Unknown",
        )

        persona_gender = _coerce_text(
            persona.get("gender")
        )

        persona_occupation = _coerce_text(
            persona.get("occupation")
        )

        persona_technology_usage = (
            _coerce_text(
                persona.get(
                    "technology_usage"
                )
            )
        )

        persona_buying_behaviour = (
            _coerce_text(
                persona.get(
                    "buying_behaviour"
                )
                or persona.get(
                    "buying_behavior"
                )
            )
        )

        fit_profile = (
            _build_weighted_product_fit(
                persona,
                product_name,
                research_goal,
            )
        )

        base_score = int(
            fit_profile[
                "overall_score"
            ]
        )

        for question_index, question in enumerate(
            questions
        ):

            category_modifier = {
                "Pricing": -4,
                "Barriers": -8,
                "Trust": -2,
                "Product Fit": 6,
                "Recommendation": 4,
                "Retention": 2,
            }.get(
                question.get(
                    "category",
                    "",
                ),
                0,
            )

            question_score = max(
                0,
                min(
                    100,
                    base_score
                    + (
                        question_index
                        * 4
                    )
                    + category_modifier,
                ),
            )

            options = question.get(
                "options",
                [],
            )

            response_value = (
                _answer_for_score(
                    question_score,
                    options,
                )
            )

            confidence_score = (
                _confidence_for_score(
                    question_score
                )
            )

            emotion = _emotion_for_score(
                question_score
            )

            reasoning = (
                f"This response reflects "
                f"{emotion} sentiment because "
                f"the persona has "
                f"{fit_profile['summary'].lower()} "
                f"and the product context aligns "
                f"with the stated goals."
            )

            responses.append(
                {
                    "persona_name": persona_name,
                    "persona_id": persona_id,
                    "persona_age": persona_age,
                    "persona_gender": persona_gender,
                    "persona_occupation": (
                        persona_occupation
                    ),
                    "persona_technology_usage": (
                        persona_technology_usage
                    ),
                    "persona_buying_behaviour": (
                        persona_buying_behaviour
                    ),
                    "question_id": question[
                        "id"
                    ],
                    "question": question[
                        "question"
                    ],
                    "question_category": (
                        question[
                            "category"
                        ]
                    ),
                    "question_type": question[
                        "type"
                    ],
                    "template_name": template_name,
                    "answer": response_value,
                    "confidence_score": (
                        confidence_score
                    ),
                    "emotion": emotion,
                    "reasoning": reasoning,
                    "timestamp": timestamp,
                    "score": question_score,
                    "product_name": product_name,
                    "research_goal": research_goal,
                    "product_fit_details": fit_profile,
                }
            )

    average_fit = (
        calculate_product_fit_score(
            responses
        )
    )

    analytics = analyze_survey_responses(
        responses
    )

    return {
        "product_name": product_name,
        "research_goal": research_goal,
        "template_name": template_name,
        "survey": questions,
        "responses": responses,
        "analytics": analytics,
        "question_categories": sorted(
            {
                question[
                    "category"
                ]
                for question in questions
            }
        ),
        "product_fit_score": average_fit,
    }


# ============================================================
# SURVEY ANALYTICS
# ============================================================

def analyze_survey_responses(
    responses: Sequence[
        Mapping[str, Any]
    ],
) -> Dict[str, Any]:

    category_scores: MutableMapping[
        str,
        List[float],
    ] = defaultdict(list)

    persona_scores: MutableMapping[
        str,
        List[float],
    ] = defaultdict(list)

    question_scores: MutableMapping[
        str,
        List[float],
    ] = defaultdict(list)

    answer_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    confidence_scores: List[float] = []
    adoption_barriers: Counter[str] = Counter()

    for response in responses:

        score = float(
            response.get(
                "score",
                0,
            )
            or 0
        )

        category = _coerce_text(
            response.get(
                "question_category"
            ),
            "General",
        )

        persona_name = _coerce_text(
            response.get(
                "persona_name"
            ),
            "Persona",
        )

        question = _coerce_text(
            response.get(
                "question_id"
            ),
            "Question",
        )

        category_scores[
            category
        ].append(score)

        persona_scores[
            persona_name
        ].append(score)

        question_scores[
            question
        ].append(score)

        answer_counter[
            _coerce_text(
                response.get("answer"),
                "N/A",
            )
        ] += 1

        sentiment_counter[
            _emotion_for_score(
                int(score)
            )
        ] += 1

        confidence_scores.append(
            float(
                response.get(
                    "confidence_score",
                    0,
                )
                or 0
            )
        )

        fit_details = response.get(
            "product_fit_details",
            {},
        )

        if isinstance(
            fit_details,
            Mapping,
        ):
            for weakness in fit_details.get(
                "weaknesses",
                [],
            ):
                adoption_barriers[
                    _coerce_text(weakness)
                ] += 1

    return {
        "average_by_category": {
            key: _safe_mean(values)
            for key, values
            in category_scores.items()
        },
        "average_by_persona": {
            key: _safe_mean(values)
            for key, values
            in persona_scores.items()
        },
        "average_by_question": {
            key: _safe_mean(values)
            for key, values
            in question_scores.items()
        },
        "answer_distribution": dict(
            answer_counter
        ),
        "sentiment_distribution": dict(
            sentiment_counter
        ),
        "average_confidence": _safe_mean(
            confidence_scores
        ),
        "adoption_barriers": dict(
            adoption_barriers.most_common(
                8
            )
        ),
        "response_count": len(
            responses
        ),
    }


def extract_insights(
    responses: Sequence[
        Mapping[str, Any]
    ],
) -> List[Dict[str, Any]]:

    grouped: MutableMapping[
        str,
        List[int],
    ] = defaultdict(list)

    grouped_questions: Dict[
        str,
        str,
    ] = {}

    for response in responses:

        question_id = str(
            response.get(
                "question_id",
                "",
            )
        )

        grouped[
            question_id
        ].append(
            int(
                response.get(
                    "score",
                    0,
                )
                or 0
            )
        )

        grouped_questions[
            question_id
        ] = str(
            response.get(
                "question",
                question_id,
            )
        )

    insights: List[
        Dict[str, Any]
    ] = []

    for question_id, scores in grouped.items():

        average = _safe_mean(
            scores
        )

        if average >= 75:
            direction = "very positive"
            summary = (
                "Product has strong market "
                "potential among the surveyed personas."
            )

        elif average >= 55:
            direction = "moderately positive"
            summary = (
                "The product shows solid promise "
                "but needs clearer value communication."
            )

        else:
            direction = "needs attention"
            summary = (
                "The product requires stronger "
                "positioning and more targeted messaging."
            )

        insights.append(
            {
                "question_id": question_id,
                "question": grouped_questions[
                    question_id
                ],
                "average_score": average,
                "insight": (
                    f"Responses for this question "
                    f"are {direction} with an average "
                    f"score of {average}."
                ),
                "summary": summary,
                "readable_summary": (
                    f"{summary} Most respondents are "
                    f"trending toward {direction} "
                    "sentiment on this question."
                ),
            }
        )

    return insights


def calculate_product_fit_score(
    responses: Sequence[
        Mapping[str, Any]
    ],
) -> float:

    if not responses:
        return 0.0

    values = [
        float(
            response.get(
                "score",
                0,
            )
            or 0
        )
        for response in responses
    ]

    return round(
        sum(values) / len(values),
        2,
    )


# ============================================================
# RESEARCH REPORT
# ============================================================

def build_research_report(
    personas: Sequence[
        Mapping[str, Any]
    ],
    responses: Sequence[
        Mapping[str, Any]
    ],
    product_name: str = "",
    research_goal: str = "",
) -> Dict[str, Any]:

    persona_items = [
        _normalize_persona(
            persona
        )
        for persona in personas
    ]

    age_values: List[int] = []
    occupation_counter: Counter[str] = Counter()
    goal_counter: Counter[str] = Counter()
    pain_counter: Counter[str] = Counter()
    buying_counter: Counter[str] = Counter()
    tech_counter: Counter[str] = Counter()
    psych_counter: Counter[str] = Counter()

    for persona in persona_items:

        age_value = persona.get(
            "age"
        )

        if isinstance(
            age_value,
            (int, float),
        ):
            age_values.append(
                int(age_value)
            )

        elif isinstance(
            age_value,
            str,
        ):
            digits = re.findall(
                r"(\d+)",
                age_value,
            )

            if digits:
                age_values.append(
                    int(digits[0])
                )

        occupation_counter[
            _coerce_text(
                persona.get(
                    "occupation"
                )
            )
        ] += 1

        for goal in _coerce_list(
            persona.get("goals")
        ):
            goal_counter[goal] += 1

        for pain in _coerce_list(
            persona.get("pain_points")
        ):
            pain_counter[pain] += 1

        for buying in _coerce_list(
            persona.get(
                "buying_behaviour"
            )
            or persona.get(
                "buying_behavior"
            )
        ):
            buying_counter[buying] += 1

        for tech in _coerce_list(
            persona.get(
                "technology_usage"
            )
        ):
            tech_counter[tech] += 1

        big_five = (
            persona.get("big_five")
            or persona.get(
                "big_five_personality"
            )
            or {}
        )

        if isinstance(
            big_five,
            Mapping,
        ):
            for key in [
                "Openness",
                "Conscientiousness",
                "Extraversion",
                "Agreeableness",
                "Neuroticism",
            ]:
                psych_counter[
                    key
                ] += _coerce_score(
                    big_five.get(
                        key.lower()
                    )
                )

    insights = extract_insights(
        responses
    )

    average_age = _safe_mean(
        age_values
    )

    average_fit = (
        calculate_product_fit_score(
            responses
        )
    )

    dominant_persona_type = (
        occupation_counter.most_common(
            1
        )[0][0]
        if occupation_counter
        else "Not available"
    )

    top_goals = [
        item[0]
        for item in goal_counter.most_common(
            3
        )
    ]

    top_pain_points = [
        item[0]
        for item in pain_counter.most_common(
            3
        )
    ]

    top_buying = [
        item[0]
        for item in buying_counter.most_common(
            3
        )
    ]

    top_tech = [
        item[0]
        for item in tech_counter.most_common(
            3
        )
    ]

    psychological_trends: Dict[
        str,
        float,
    ] = {}

    if psych_counter:
        psychological_trends = {
            key: round(
                value
                / max(
                    len(persona_items),
                    1,
                ),
                2,
            )
            for key, value
            in psych_counter.items()
        }

    return {
        "research_overview": {
            "product_name": product_name,
            "research_goal": research_goal,
            "total_personas": len(
                persona_items
            ),
            "surveys_executed": len(
                {
                    response.get(
                        "question_id",
                        "",
                    )
                    for response in responses
                }
            ),
            "average_product_fit": average_fit,
            "average_age": average_age,
            "dominant_persona_type": (
                dominant_persona_type
            ),
        },
        "persona_summary": {
            "age_distribution": age_values,
            "occupation_summary": dict(
                occupation_counter
            ),
            "top_goals": top_goals,
            "top_pain_points": (
                top_pain_points
            ),
            "buying_behaviour": top_buying,
            "technology_usage": top_tech,
        },
        "psychological_trends": (
            psychological_trends
        ),
        "product_fit_analysis": {
            "overall_score": average_fit,
            "key_insights": insights,
        },
        "key_insights": [
            insight.get(
                "readable_summary",
                insight.get(
                    "insight",
                    "",
                ),
            )
            for insight in insights
        ],
        "final_recommendation": (
            "The product demonstrates adoption "
            "potential among the current persona mix. "
            "Pair value-oriented messaging with a "
            "low-friction experience and address "
            "the highest-scoring adoption barriers."
        ),
    }


def build_dashboard_payload(
    responses: Sequence[
        Mapping[str, Any]
    ],
    personas: Optional[
        Sequence[Mapping[str, Any]]
    ] = None,
    product_name: str = "",
    research_goal: str = "",
) -> Dict[str, Any]:

    insights = extract_insights(
        responses
    )

    average_fit = (
        calculate_product_fit_score(
            responses
        )
    )

    persona_list = [
        _normalize_persona(
            persona
        )
        for persona in (
            personas or []
        )
    ]

    summary = build_research_report(
        persona_list,
        responses,
        product_name=product_name,
        research_goal=research_goal,
    )

    return {
        "insights": insights,
        "product_fit_score": average_fit,
        "response_count": len(
            responses
        ),
        "survey_count": len(
            {
                response.get(
                    "question_id",
                    "",
                )
                for response in responses
            }
        ),
        "research_report": summary,
        "kpis": {
            "total_personas": len(
                persona_list
            ),
            "surveys_executed": len(
                {
                    response.get(
                        "question_id",
                        "",
                    )
                    for response in responses
                }
            ),
            "average_product_fit": (
                average_fit
            ),
            "average_age": summary[
                "research_overview"
            ]["average_age"],
            "average_satisfaction": (
                average_fit
            ),
            "dominant_persona_type": (
                summary[
                    "research_overview"
                ]["dominant_persona_type"]
            ),
        },
    }


# ============================================================
# PDF EXPORT
# ============================================================

def export_research_report_pdf(
    report: Mapping[str, Any],
) -> bytes:

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import (
            getSampleStyleSheet,
        )
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
    except Exception:
        return b""

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
    )

    styles = getSampleStyleSheet()

    story = [
        Paragraph(
            "Synthetic User Generation Platform - Research Report",
            styles["Title"],
        ),
        Spacer(1, 12),
    ]

    overview = report.get(
        "research_overview",
        {},
    )

    persona_summary = report.get(
        "persona_summary",
        {},
    )

    fit_analysis = report.get(
        "product_fit_analysis",
        {},
    )

    story.append(
        Paragraph(
            f"Product: {overview.get('product_name', 'N/A')}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"Research Goal: {overview.get('research_goal', 'N/A')}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"Total Personas: {overview.get('total_personas', 0)}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"Average Product Fit: {overview.get('average_product_fit', 0)}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"Average Age: {overview.get('average_age', 0)}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"Dominant Persona Type: {overview.get('dominant_persona_type', 'N/A')}",
            styles["BodyText"],
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "Persona Summary",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            "Occupation Summary: "
            + json.dumps(
                persona_summary.get(
                    "occupation_summary",
                    {},
                )
            ),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Top Goals: "
            + (
                ", ".join(
                    persona_summary.get(
                        "top_goals",
                        [],
                    )
                )
                or "N/A"
            ),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Top Pain Points: "
            + (
                ", ".join(
                    persona_summary.get(
                        "top_pain_points",
                        [],
                    )
                )
                or "N/A"
            ),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Buying Behaviour: "
            + (
                ", ".join(
                    persona_summary.get(
                        "buying_behaviour",
                        [],
                    )
                )
                or "N/A"
            ),
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            "Technology Usage: "
            + (
                ", ".join(
                    persona_summary.get(
                        "technology_usage",
                        [],
                    )
                )
                or "N/A"
            ),
            styles["BodyText"],
        )
    )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "Product Fit Analysis",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            f"Overall Score: {fit_analysis.get('overall_score', 0)}",
            styles["BodyText"],
        )
    )

    for insight in fit_analysis.get(
        "key_insights",
        [],
    ):
        story.append(
            Paragraph(
                "- "
                + str(
                    insight.get(
                        "readable_summary",
                        insight.get(
                            "insight",
                            "",
                        ),
                    )
                ),
                styles["BodyText"],
            )
        )

    story.append(
        Spacer(1, 10)
    )

    story.append(
        Paragraph(
            "Final Recommendation",
            styles["Heading2"],
        )
    )

    story.append(
        Paragraph(
            str(
                report.get(
                    "final_recommendation",
                    "",
                )
            ),
            styles["BodyText"],
        )
    )

    document.build(story)

    return buffer.getvalue()


# Compatibility name used by some dashboard/report code.
def export_full_research_report_pdf(
    experiment: Mapping[str, Any],
    personas: Sequence[
        Mapping[str, Any]
    ],
    survey_results: Optional[
        Mapping[str, Any]
    ] = None,
    interview_rows: Optional[
        Sequence[Mapping[str, Any]]
    ] = None,
    insights: Optional[
        Mapping[str, Any]
    ] = None,
) -> bytes:

    survey_results = (
        survey_results or {}
    )

    responses = survey_results.get(
        "responses",
        [],
    )

    product_name = str(
        experiment.get(
            "product_name",
            survey_results.get(
                "product_name",
                "",
            ),
        )
    )

    research_goal = str(
        experiment.get(
            "research_objective",
            survey_results.get(
                "research_goal",
                "",
            ),
        )
    )

    report = build_research_report(
        personas,
        responses,
        product_name=product_name,
        research_goal=research_goal,
    )

    report["interview_results"] = (
        list(interview_rows or [])
    )

    report["insights"] = dict(
        insights or {}
    )

    return export_research_report_pdf(
        report
    )


# ============================================================
# DEMO DATASET
# ============================================================

def generate_demo_dataset(
    product_name: str = "FitPulse AI",
    research_goal: str = (
        "Understand retention barriers and "
        "product adoption intent."
    ),
) -> Dict[str, Any]:

    personas = [
        {
            "id": "demo-1",
            "name": "Aarav Sharma",
            "age": 26,
            "gender": "Male",
            "occupation": "Software Engineer",
            "education": "Bachelor's Degree",
            "income": "$75k",
            "company": "Tech Startup",
            "goals": [
                "Improve productivity",
                "Stay healthy",
                "Learn new tools",
            ],
            "pain_points": [
                "Time pressure",
                "Low motivation",
                "Incomplete routines",
            ],
            "traits": [
                "Driven",
                "Curious",
                "Tech-savvy",
            ],
            "behaviour": [
                "Uses mobile apps daily",
                "Prefers automation",
                "Likes short sessions",
            ],
            "technology_usage": "High",
            "buying_behaviour": (
                "Value-driven and mobile-first"
            ),
            "psychological_profile": (
                "Motivated by clear outcomes and efficiency"
            ),
            "behavior_pattern": (
                "Prefers quick, measurable progress"
            ),
            "big_five": {
                "openness": 85,
                "conscientiousness": 72,
                "extraversion": 60,
                "agreeableness": 63,
                "neuroticism": 30,
            },
        },
        {
            "id": "demo-2",
            "name": "Meera Patel",
            "age": 29,
            "gender": "Female",
            "occupation": "Student",
            "education": "Graduate Student",
            "income": "$35k",
            "company": "University",
            "goals": [
                "Build discipline",
                "Stay consistent",
                "Manage stress",
            ],
            "pain_points": [
                "Overwhelm",
                "Poor routine structure",
                "Busy schedule",
            ],
            "traits": [
                "Ambitious",
                "Adaptive",
                "Resilient",
            ],
            "behaviour": [
                "Uses mobile-first tools",
                "Responds to social proof",
                "Likes simple guidance",
            ],
            "technology_usage": "Medium-High",
            "buying_behaviour": (
                "Affordable and simple"
            ),
            "psychological_profile": (
                "Responsive to motivation and social encouragement"
            ),
            "behavior_pattern": (
                "Wants quick wins and guided routines"
            ),
            "big_five": {
                "openness": 78,
                "conscientiousness": 68,
                "extraversion": 58,
                "agreeableness": 80,
                "neuroticism": 42,
            },
        },
        {
            "id": "demo-3",
            "name": "Lucas Reed",
            "age": 41,
            "gender": "Male",
            "occupation": "Operations Manager",
            "education": "MBA",
            "income": "$110k",
            "company": "Retail Chain",
            "goals": [
                "Reduce team friction",
                "Drive productivity",
                "Improve retention",
            ],
            "pain_points": [
                "Manual tracking",
                "Lack of insight",
                "Operational delays",
            ],
            "traits": [
                "Structured",
                "Analytical",
                "Goal-oriented",
            ],
            "behaviour": [
                "Works across dashboards",
                "Values analytics",
                "Prefers reliable systems",
            ],
            "technology_usage": "High",
            "buying_behaviour": (
                "Trust-based and ROI focused"
            ),
            "psychological_profile": (
                "Values measurable business outcomes"
            ),
            "behavior_pattern": (
                "Prefers systems that reduce operational friction"
            ),
            "big_five": {
                "openness": 70,
                "conscientiousness": 85,
                "extraversion": 55,
                "agreeableness": 67,
                "neuroticism": 25,
            },
        },
        {
            "id": "demo-4",
            "name": "Sofia Nair",
            "age": 34,
            "gender": "Female",
            "occupation": "Healthcare Professional",
            "education": "RN",
            "income": "$82k",
            "company": "Private Clinic",
            "goals": [
                "Improve wellness",
                "Stay organized",
                "Reduce stress",
            ],
            "pain_points": [
                "Long shifts",
                "No time for planning",
                "Low energy",
            ],
            "traits": [
                "Compassionate",
                "Focused",
                "Reliable",
            ],
            "behaviour": [
                "Prefers mobile nudges",
                "Trusts evidence-based products",
                "Values flexibility",
            ],
            "technology_usage": "Medium",
            "buying_behaviour": (
                "Trust-centered and pragmatic"
            ),
            "psychological_profile": (
                "Seeks balance and practical support"
            ),
            "behavior_pattern": (
                "Prefers short, relevant interactions"
            ),
            "big_five": {
                "openness": 74,
                "conscientiousness": 76,
                "extraversion": 49,
                "agreeableness": 84,
                "neuroticism": 35,
            },
        },
    ]

    survey_result = execute_survey(
        personas,
        product_name=product_name,
        research_goal=research_goal,
    )

    report = build_research_report(
        personas,
        survey_result["responses"],
        product_name=product_name,
        research_goal=research_goal,
    )

    return {
        "personas": personas,
        "survey_results": survey_result,
        "research_report": report,
    }


if __name__ == "__main__":
    demo = generate_demo_dataset()

    print(
        json.dumps(
            {
                "persona_count": len(
                    demo["personas"]
                ),
                "response_count": len(
                    demo["survey_results"][
                        "responses"
                    ]
                ),
                "product_fit_score": demo[
                    "survey_results"
                ][
                    "product_fit_score"
                ],
            },
            indent=2,
        )
    )
