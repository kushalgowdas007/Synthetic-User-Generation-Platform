from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

DEFAULT_SURVEY_QUESTIONS = [
    {
        "id": "q1",
        "question": "How important is a smooth onboarding experience for the product?",
        "category": "Onboarding",
        "type": "single_choice",
        "options": ["Not important", "Somewhat important", "Important", "Very important"],
        "weight": 1,
    },
    {
        "id": "q2",
        "question": "How likely are you to adopt a solution that reduces your current pain points?",
        "category": "Adoption",
        "type": "single_choice",
        "options": ["Very unlikely", "Unlikely", "Possible", "Very likely"],
        "weight": 1,
    },
    {
        "id": "q3",
        "question": "How likely are you to recommend this product to peers after trying it?",
        "category": "Recommendation",
        "type": "single_choice",
        "options": ["No", "Maybe", "Likely", "Highly likely"],
        "weight": 1,
    },
]

SURVEY_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "Product Adoption": DEFAULT_SURVEY_QUESTIONS,
    "Usability and Onboarding": [
        {
            "id": "u1",
            "question": "How easy would it be for you to understand the first step in this product?",
            "category": "Usability",
            "type": "single_choice",
            "options": ["Very hard", "Somewhat hard", "Easy", "Very easy"],
            "weight": 1,
        },
        {
            "id": "u2",
            "question": "How much guidance would you expect during setup?",
            "category": "Onboarding",
            "type": "single_choice",
            "options": ["None", "A little", "Guided setup", "Hands-on support"],
            "weight": 1,
        },
        {
            "id": "u3",
            "question": "Would unclear navigation stop you from using this product regularly?",
            "category": "Barriers",
            "type": "single_choice",
            "options": ["Definitely", "Probably", "Not much", "Not at all"],
            "weight": 1,
        },
        {
            "id": "u4",
            "question": "How confident would you feel completing your main task without support?",
            "category": "Confidence",
            "type": "single_choice",
            "options": ["Not confident", "Somewhat confident", "Confident", "Very confident"],
            "weight": 1,
        },
    ],
    "Pricing Sensitivity": [
        {
            "id": "p1",
            "question": "How important is transparent pricing before you try this product?",
            "category": "Pricing",
            "type": "single_choice",
            "options": ["Not important", "Somewhat important", "Important", "Critical"],
            "weight": 1,
        },
        {
            "id": "p2",
            "question": "Would a free trial increase your willingness to adopt this product?",
            "category": "Trial",
            "type": "single_choice",
            "options": ["No", "Maybe", "Likely", "Definitely"],
            "weight": 1,
        },
        {
            "id": "p3",
            "question": "How much proof of ROI would you need before paying?",
            "category": "Trust",
            "type": "single_choice",
            "options": ["Very little", "Some proof", "Strong proof", "Detailed proof"],
            "weight": 1,
        },
        {
            "id": "p4",
            "question": "Would bundled features make the price feel more acceptable?",
            "category": "Value",
            "type": "single_choice",
            "options": ["No", "Maybe", "Likely", "Definitely"],
            "weight": 1,
        },
    ],
    "Retention and Loyalty": [
        {
            "id": "r1",
            "question": "How likely are you to keep using this product after the first month?",
            "category": "Retention",
            "type": "single_choice",
            "options": ["Unlikely", "Maybe", "Likely", "Very likely"],
            "weight": 1,
        },
        {
            "id": "r2",
            "question": "Which factor would most influence repeat usage?",
            "category": "Behavior",
            "type": "single_choice",
            "options": ["Price", "Ease of use", "Outcome quality", "Habit formation"],
            "weight": 1,
        },
        {
            "id": "r3",
            "question": "Would reminders or progress tracking help you stay engaged?",
            "category": "Engagement",
            "type": "single_choice",
            "options": ["No", "Maybe", "Likely", "Definitely"],
            "weight": 1,
        },
        {
            "id": "r4",
            "question": "How likely are you to switch away if setup takes too long?",
            "category": "Barriers",
            "type": "single_choice",
            "options": ["Very likely", "Likely", "Maybe", "Unlikely"],
            "weight": 1,
        },
    ],
    "Feature Discovery": [
        {
            "id": "f1",
            "question": "Which feature type would create the strongest first impression?",
            "category": "Feature Request",
            "type": "single_choice",
            "options": ["Automation", "Analytics", "Personalization", "Collaboration"],
            "weight": 1,
        },
        {
            "id": "f2",
            "question": "How important is personalization to your adoption decision?",
            "category": "Personalization",
            "type": "single_choice",
            "options": ["Not important", "Somewhat important", "Important", "Very important"],
            "weight": 1,
        },
        {
            "id": "f3",
            "question": "Would integrations with current tools increase fit?",
            "category": "Integration",
            "type": "single_choice",
            "options": ["No", "Maybe", "Likely", "Definitely"],
            "weight": 1,
        },
        {
            "id": "f4",
            "question": "What level of automation would feel trustworthy?",
            "category": "Trust",
            "type": "single_choice",
            "options": ["Manual only", "Suggestions", "Assisted automation", "Full automation"],
            "weight": 1,
        },
    ],
}


def _normalize_persona(persona: Any) -> Dict[str, Any]:
    """Normalize a Persona-like object into a dictionary for survey analysis."""
    if isinstance(persona, Mapping):
        return dict(persona)

    if hasattr(persona, "to_dict"):
        try:
            return dict(persona.to_dict())
        except Exception:
            pass

    return {}


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def _coerce_text(value: Any, default: str = "Not provided") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.strip()
        return text or default
    return str(value).strip() or default


def _coerce_score(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    try:
        return float(text)
    except ValueError:
        return default


def _safe_mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _word_tokens(value: Any) -> List[str]:
    text = str(value or "")
    return [token.lower() for token in re.findall(r"[a-zA-Z]+", text) if len(token) > 2]


def _overlap_score(text: str, keywords: Sequence[str]) -> float:
    source_tokens = set(_word_tokens(text))
    target_tokens = set(token.lower() for token in keywords if token)
    if not target_tokens:
        return 0.0
    overlap = len(source_tokens.intersection(target_tokens))
    return min(100.0, round((overlap / max(len(target_tokens), 1)) * 100.0, 2))


def _strongest_summary(summary_map: Mapping[str, float]) -> str:
    if not summary_map:
        return "No dominant pattern yet"
    strongest = max(summary_map.items(), key=lambda item: item[1])
    return f"{strongest[0]} is the strongest observed signal"


def _normalize_question(question: Any, index: int, product_name: str, research_goal: str) -> Dict[str, Any]:
    if isinstance(question, Mapping):
        source = dict(question)
        text = _coerce_text(source.get("question") or source.get("text"), "How helpful is this product?")
        options = source.get("options") or ["Very unlikely", "Unlikely", "Likely", "Very likely"]
        question_type = _coerce_text(source.get("type"), "single_choice")
        category = _coerce_text(source.get("category"), "General")
        weight = int(_coerce_score(source.get("weight"), 1) or 1)
        question_id = _coerce_text(source.get("id"), f"q{index + 1}")
    else:
        text = _coerce_text(question, "How helpful is this product?")
        options = ["Very unlikely", "Unlikely", "Likely", "Very likely"]
        question_type = "single_choice"
        category = "Custom"
        weight = 1
        question_id = f"custom_{index + 1}"

    return {
        "id": question_id,
        "question": text,
        "category": category,
        "type": question_type,
        "options": list(options) if isinstance(options, (list, tuple)) else _coerce_list(options),
        "weight": max(1, weight),
        "product_name": str(product_name or ""),
        "research_goal": str(research_goal or ""),
    }


def _dynamic_questions(product_name: str, research_goal: str) -> List[Dict[str, Any]]:
    product_label = product_name.strip() or "this product"
    goal_label = research_goal.strip() or "your main goal"
    return [
        {
            "id": "dyn_goal_fit",
            "question": f"How well does {product_label} support {goal_label}?",
            "category": "Product Fit",
            "type": "single_choice",
            "options": ["Poorly", "Somewhat", "Well", "Very well"],
            "weight": 2,
        },
        {
            "id": "dyn_barrier",
            "question": f"What would most prevent you from adopting {product_label}?",
            "category": "Barriers",
            "type": "single_choice",
            "options": ["Price", "Trust", "Learning curve", "Low need"],
            "weight": 2,
        },
    ]


def _build_weighted_product_fit(persona: Mapping[str, Any], product_name: str, research_goal: str) -> Dict[str, Any]:
    goals = " ".join(_coerce_list(persona.get("goals")))
    pain_points = " ".join(_coerce_list(persona.get("pain_points")))
    behaviour = " ".join(_coerce_list(persona.get("behaviour") or persona.get("behavior")))
    tech_usage = _coerce_text(persona.get("technology_usage"), "Not provided")
    buying_behaviour = _coerce_text(persona.get("buying_behaviour") or persona.get("buying_behavior"), "Not provided")
    occupation = _coerce_text(persona.get("occupation"), "Not provided")

    big_five = persona.get("big_five") or persona.get("big_five_personality") or {}
    if isinstance(big_five, Mapping):
        openness = _coerce_score(big_five.get("openness"), 0.0)
        conscientiousness = _coerce_score(big_five.get("conscientiousness"), 0.0)
        extraversion = _coerce_score(big_five.get("extraversion"), 0.0)
        agreeableness = _coerce_score(big_five.get("agreeableness"), 0.0)
        neuroticism = _coerce_score(big_five.get("neuroticism"), 0.0)
    else:
        openness = conscientiousness = extraversion = agreeableness = neuroticism = 0.0

    product_context = f"{product_name} {research_goal}".lower()

    pain_point_keywords = [
        "value", "affordability", "price", "budget", "cost",
        "time", "ease", "friction", "complexity", "stress", "motivation",
        "convenience", "trust", "integration", "speed", "learning"
    ]
    goal_keywords = [
        "career", "success", "growth", "health", "wellness", "efficiency",
        "learning", "retention", "productivity", "automation", "mobility", "insight"
    ]
    tech_keywords = ["mobile", "desktop", "ai", "automation", "cloud", "analytics", "app", "wearable"]
    buying_keywords = ["affordability", "value", "quality", "convenience", "easy", "trust", "speed"]
    industry_keywords = ["health", "finance", "education", "retail", "technology", "travel", "media"]

    pain_point_match = _overlap_score(f"{pain_points} {product_context}", pain_point_keywords)
    goal_match = _overlap_score(f"{goals} {product_context}", goal_keywords)
    technology_match = _overlap_score(f"{tech_usage} {product_context}", tech_keywords)
    buying_behaviour_score = _overlap_score(f"{buying_behaviour} {behaviour} {product_context}", buying_keywords)
    psychological_alignment = min(100.0, round(((openness + conscientiousness + extraversion + agreeableness) / 4.0) * 0.8 + (100 - neuroticism) * 0.2, 2))
    industry_alignment = _overlap_score(f"{occupation} {product_context}", industry_keywords)

    weights = {
        "Pain Point Match": 0.18,
        "Goal Match": 0.18,
        "Technology Match": 0.15,
        "Buying Behaviour": 0.14,
        "Psychological Alignment": 0.17,
        "Industry Alignment": 0.18,
    }

    category_scores = {
        "Pain Point Match": round(pain_point_match, 2),
        "Goal Match": round(goal_match, 2),
        "Technology Match": round(technology_match, 2),
        "Buying Behaviour": round(buying_behaviour_score, 2),
        "Psychological Alignment": round(psychological_alignment, 2),
        "Industry Alignment": round(industry_alignment, 2),
    }

    overall_compatibility = round(
        sum(category_scores[key] * weights[key] for key in category_scores),
        2,
    )

    strengths = []
    weaknesses = []
    recommendations = []

    for key, score in category_scores.items():
        if score >= 70:
            strengths.append(key)
        elif score < 45:
            weaknesses.append(key)

    if not weaknesses:
        weaknesses.append("No major risk flags detected")

    if any(item in strengths for item in ("Goal Match", "Pain Point Match")):
        recommendations.append("Position the product around high-value, low-friction outcomes that directly address the persona's stated goals.")
    if "Technology Match" in strengths:
        recommendations.append("Keep the mobile-first and automation-first experience as a central selling message.")
    if "Buying Behaviour" in weaknesses:
        recommendations.append("Reinforce affordability and clarity in messaging to improve conversion intent.")
    if "Psychological Alignment" in weaknesses:
        recommendations.append("Use onboarding nudges and trust-building content to reduce hesitation and improve adoption confidence.")

    return {
        "overall_score": round(overall_compatibility, 2),
        "category_scores": category_scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "summary": _strongest_summary(category_scores),
    }


def _answer_for_score(score: int, options: Sequence[str]) -> str:
    if score >= 85:
        return options[-1] if options else "Highly likely"
    if score >= 65:
        return options[-2] if len(options) > 1 else options[-1]
    if score >= 45:
        return options[-3] if len(options) > 2 else options[-1]
    return options[0] if options else "Not important"


def _confidence_for_score(score: int) -> int:
    return max(60, min(98, int(score)))


def _emotion_for_score(score: int) -> str:
    if score >= 80:
        return "excited"
    if score >= 60:
        return "positive"
    if score >= 40:
        return "neutral"
    return "cautious"


def create_survey(
    product_name: str = "",
    research_goal: str = "",
    survey_questions: Optional[Sequence[Any]] = None,
    template_name: str = "Product Adoption",
    include_dynamic_questions: bool = False,
) -> List[Dict[str, Any]]:
    """Create a survey payload for the current product and research objective."""
    template_questions = SURVEY_TEMPLATES.get(template_name, DEFAULT_SURVEY_QUESTIONS)
    questions = list(survey_questions) if survey_questions is not None else list(template_questions)
    if include_dynamic_questions:
        questions.extend(_dynamic_questions(product_name, research_goal))
    return [
        _normalize_question(question, index, product_name, research_goal)
        for index, question in enumerate(questions)
    ]


def execute_survey(
    personas: Any,
    product_name: str = "",
    research_goal: str = "",
    survey_questions: Optional[Sequence[Any]] = None,
    template_name: str = "Product Adoption",
    include_dynamic_questions: bool = False,
) -> Dict[str, Any]:
    """Execute the survey and enrich each response with realistic reasoning metadata."""
    if personas is None:
        normalized_personas: List[Dict[str, Any]] = []
    elif isinstance(personas, Mapping):
        normalized_personas = [_normalize_persona(personas)]
    elif isinstance(personas, list):
        normalized_personas = [_normalize_persona(persona) for persona in personas if persona is not None]
    else:
        normalized_personas = [_normalize_persona(personas)]

    questions = create_survey(
        product_name=product_name,
        research_goal=research_goal,
        survey_questions=survey_questions,
        template_name=template_name,
        include_dynamic_questions=include_dynamic_questions,
    )
    responses: List[Dict[str, Any]] = []

    for index, persona in enumerate(normalized_personas):
        persona_name = _coerce_text(persona.get("name"), f"Persona {index + 1}")
        persona_id = _coerce_text(persona.get("id") or f"persona-{index + 1}", f"persona-{index + 1}")
        persona_age = _coerce_text(persona.get("age"), "Unknown")
        persona_gender = _coerce_text(persona.get("gender"), "Not provided")
        persona_occupation = _coerce_text(persona.get("occupation"), "Not provided")
        persona_technology_usage = _coerce_text(persona.get("technology_usage"), "Not provided")
        persona_buying_behaviour = _coerce_text(
            persona.get("buying_behaviour") or persona.get("buying_behavior"),
            "Not provided",
        )

        fit_profile = _build_weighted_product_fit(persona, product_name, research_goal)
        base_score = int(fit_profile["overall_score"])

        for question_index, question in enumerate(questions):
            category_modifier = {
                "Pricing": -4,
                "Barriers": -8,
                "Trust": -2,
                "Product Fit": 6,
                "Recommendation": 4,
                "Retention": 2,
            }.get(question.get("category", ""), 0)
            question_score = max(0, min(100, base_score + (question_index * 4) + category_modifier))
            response_value = _answer_for_score(question_score, question.get("options", []))
            confidence_score = _confidence_for_score(question_score)
            emotion = _emotion_for_score(question_score)
            reasoning = (
                f"This response reflects {emotion} sentiment because the persona has strong alignment with "
                f"{fit_profile['summary'].lower()} and the product context is a clear fit for the stated goals."
            )
            timestamp = datetime.now(timezone.utc).isoformat()

            responses.append(
                {
                    "persona_name": persona_name,
                    "persona_id": persona_id,
                    "persona_age": persona_age,
                    "persona_gender": persona_gender,
                    "persona_occupation": persona_occupation,
                    "persona_technology_usage": persona_technology_usage,
                    "persona_buying_behaviour": persona_buying_behaviour,
                    "question_id": question["id"],
                    "question": question["question"],
                    "question_category": question["category"],
                    "question_type": question["type"],
                    "template_name": template_name,
                    "answer": response_value,
                    "confidence_score": confidence_score,
                    "emotion": emotion,
                    "reasoning": reasoning,
                    "timestamp": timestamp,
                    "score": question_score,
                    "product_name": product_name,
                    "research_goal": research_goal,
                    "product_fit_details": fit_profile,
                }
            )

    average_fit = _safe_mean([float(response.get("score", 0) or 0) for response in responses]) if responses else 0.0
    analytics = analyze_survey_responses(responses)
    return {
        "product_name": product_name,
        "research_goal": research_goal,
        "template_name": template_name,
        "survey": questions,
        "responses": responses,
        "analytics": analytics,
        "question_categories": sorted({question["category"] for question in questions}),
        "product_fit_score": average_fit,
    }


def analyze_survey_responses(responses: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Aggregate survey rows for dashboard cards, charts, and exports."""
    category_scores: MutableMapping[str, List[float]] = defaultdict(list)
    persona_scores: MutableMapping[str, List[float]] = defaultdict(list)
    question_scores: MutableMapping[str, List[float]] = defaultdict(list)
    answer_counter: Counter[str] = Counter()
    sentiment_counter: Counter[str] = Counter()
    confidence_scores: List[float] = []
    adoption_barriers: Counter[str] = Counter()

    for response in responses:
        score = float(response.get("score", 0) or 0)
        category = _coerce_text(response.get("question_category"), "General")
        persona_name = _coerce_text(response.get("persona_name"), "Persona")
        question = _coerce_text(response.get("question_id"), "Question")
        category_scores[category].append(score)
        persona_scores[persona_name].append(score)
        question_scores[question].append(score)
        answer_counter[_coerce_text(response.get("answer"), "N/A")] += 1
        sentiment_counter[_emotion_for_score(int(score))] += 1
        confidence_scores.append(float(response.get("confidence_score", 0) or 0))

        fit_details = response.get("product_fit_details", {})
        if isinstance(fit_details, Mapping):
            for weakness in fit_details.get("weaknesses", []):
                adoption_barriers[_coerce_text(weakness)] += 1

    return {
        "average_by_category": {key: _safe_mean(values) for key, values in category_scores.items()},
        "average_by_persona": {key: _safe_mean(values) for key, values in persona_scores.items()},
        "average_by_question": {key: _safe_mean(values) for key, values in question_scores.items()},
        "answer_distribution": dict(answer_counter),
        "sentiment_distribution": dict(sentiment_counter),
        "average_confidence": _safe_mean(confidence_scores),
        "adoption_barriers": dict(adoption_barriers.most_common(8)),
        "response_count": len(responses),
    }


def extract_insights(responses: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Produce structured insight records with readable summaries."""
    grouped: MutableMapping[str, List[int]] = defaultdict(list)
    grouped_questions: MutableMapping[str, str] = {}

    for response in responses:
        question_id = str(response.get("question_id", ""))
        grouped[question_id].append(int(response.get("score", 0) or 0))
        grouped_questions[question_id] = str(response.get("question", question_id))

    insights: List[Dict[str, Any]] = []
    for question_id, scores in grouped.items():
        avg = _safe_mean(scores)
        if avg >= 75:
            direction = "very positive"
            summary = "Product has strong market potential among the surveyed personas."
        elif avg >= 55:
            direction = "moderately positive"
            summary = "The product shows solid promise but needs clearer value communication."
        else:
            direction = "needs attention"
            summary = "The product requires stronger positioning and more targeted messaging."

        insights.append(
            {
                "question_id": question_id,
                "question": grouped_questions[question_id],
                "average_score": avg,
                "insight": f"Responses for this question are {direction} with an average score of {avg}.",
                "summary": summary,
                "readable_summary": f"{summary} Most respondents are trending toward {direction} sentiment on this question.",
            }
        )

    return insights


def calculate_product_fit_score(responses: Sequence[Mapping[str, Any]]) -> float:
    """Return the overall product fit score for a completed survey."""
    if not responses:
        return 0.0
    values = [float(response.get("score", 0) or 0) for response in responses]
    return round(sum(values) / len(values), 2)


def build_research_report(
    personas: Sequence[Mapping[str, Any]],
    responses: Sequence[Mapping[str, Any]],
    product_name: str = "",
    research_goal: str = "",
) -> Dict[str, Any]:
    """Create an executive-style research report from personas and survey responses."""
    persona_items = [_normalize_persona(persona) for persona in personas]
    age_values = []
    occupation_counter: Counter[str] = Counter()
    goal_counter: Counter[str] = Counter()
    pain_counter: Counter[str] = Counter()
    buying_counter: Counter[str] = Counter()
    tech_counter: Counter[str] = Counter()
    psych_counter: Counter[str] = Counter()

    for persona in persona_items:
        age_value = persona.get("age")
        if isinstance(age_value, (int, float)):
            age_values.append(int(age_value))
        elif isinstance(age_value, str):
            digits = re.findall(r"(\d+)", age_value)
            if digits:
                age_values.append(int(digits[0]))
        occupation_counter[_coerce_text(persona.get("occupation"), "Not provided")] += 1
        for goal in _coerce_list(persona.get("goals")):
            goal_counter[goal] += 1
        for pain in _coerce_list(persona.get("pain_points")):
            pain_counter[pain] += 1
        for buy in _coerce_list(persona.get("buying_behaviour") or persona.get("buying_behavior")):
            buying_counter[buy] += 1
        for tech in _coerce_list(persona.get("technology_usage")):
            tech_counter[tech] += 1

        big_five = persona.get("big_five") or persona.get("big_five_personality") or {}
        if isinstance(big_five, Mapping):
            psych_counter["Openness"] += _coerce_score(big_five.get("openness"), 0.0)
            psych_counter["Conscientiousness"] += _coerce_score(big_five.get("conscientiousness"), 0.0)
            psych_counter["Extraversion"] += _coerce_score(big_five.get("extraversion"), 0.0)
            psych_counter["Agreeableness"] += _coerce_score(big_five.get("agreeableness"), 0.0)
            psych_counter["Neuroticism"] += _coerce_score(big_five.get("neuroticism"), 0.0)

    insights = extract_insights(responses)
    average_age = _safe_mean(age_values)
    average_fit = calculate_product_fit_score(responses)
    dominant_persona_type = occupation_counter.most_common(1)[0][0] if occupation_counter else "Not available"
    top_goals = [item[0] for item in goal_counter.most_common(3)]
    top_pain_points = [item[0] for item in pain_counter.most_common(3)]
    top_buying = [item[0] for item in buying_counter.most_common(3)]
    top_tech = [item[0] for item in tech_counter.most_common(3)]

    psychological_trends = {}
    if psych_counter:
        psychological_trends = {
            key: round(value / max(len(persona_items), 1), 2)
            for key, value in psych_counter.items()
        }

    research_report = {
        "research_overview": {
            "product_name": product_name,
            "research_goal": research_goal,
            "total_personas": len(persona_items),
            "surveys_executed": len(set(response.get("question_id", "") for response in responses)),
            "average_product_fit": average_fit,
            "average_age": average_age,
            "dominant_persona_type": dominant_persona_type,
        },
        "persona_summary": {
            "age_distribution": age_values,
            "occupation_summary": dict(occupation_counter),
            "top_goals": top_goals,
            "top_pain_points": top_pain_points,
            "buying_behaviour": top_buying,
            "technology_usage": top_tech,
        },
        "psychological_trends": psychological_trends,
        "product_fit_analysis": {
            "overall_score": average_fit,
            "key_insights": insights,
        },
        "key_insights": [insight.get("readable_summary", insight.get("insight", "")) for insight in insights],
        "final_recommendation": (
            "The product demonstrates strong adoption potential among the current persona mix, "
            "but the report suggests pairing value-oriented messaging with a mobile-first, low-friction experience."
        ),
    }

    return research_report


def build_dashboard_payload(
    responses: Sequence[Mapping[str, Any]],
    personas: Optional[Sequence[Mapping[str, Any]]] = None,
    product_name: str = "",
    research_goal: str = "",
) -> Dict[str, Any]:
    """Prepare a professional analytics payload expected by the dashboard page."""
    insights = extract_insights(responses)
    average_fit = calculate_product_fit_score(responses)
    persona_list = [_normalize_persona(persona) for persona in personas or []]
    summary = build_research_report(persona_list, responses, product_name=product_name, research_goal=research_goal)

    return {
        "insights": insights,
        "product_fit_score": average_fit,
        "response_count": len(responses),
        "survey_count": len(set(response.get("question_id", "") for response in responses)),
        "research_report": summary,
        "kpis": {
            "total_personas": len(persona_list),
            "surveys_executed": len(set(response.get("question_id", "") for response in responses)),
            "average_product_fit": average_fit,
            "average_age": summary["research_overview"]["average_age"],
            "average_satisfaction": average_fit,
            "dominant_persona_type": summary["research_overview"]["dominant_persona_type"],
        },
    }


def export_research_report_pdf(report: Mapping[str, Any]) -> bytes:
    """Generate a lightweight PDF report for the dashboard export action."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return b""

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Synthetic User Generation Platform — Research Report", styles["Title"]), Spacer(1, 12)]

    overview = report.get("research_overview", {})
    persona_summary = report.get("persona_summary", {})
    fit_analysis = report.get("product_fit_analysis", {})
    key_insights = report.get("key_insights", [])
    final_recommendation = report.get("final_recommendation", "")

    story.append(Paragraph(f"Product: {overview.get('product_name', 'N/A')}", styles["BodyText"]))
    story.append(Paragraph(f"Research Goal: {overview.get('research_goal', 'N/A')}", styles["BodyText"]))
    story.append(Paragraph(f"Total Personas: {overview.get('total_personas', 0)}", styles["BodyText"]))
    story.append(Paragraph(f"Average Product Fit: {overview.get('average_product_fit', 0)}", styles["BodyText"]))
    story.append(Paragraph(f"Average Age: {overview.get('average_age', 0)}", styles["BodyText"]))
    story.append(Paragraph(f"Dominant Persona Type: {overview.get('dominant_persona_type', 'N/A')}", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Persona Summary", styles["Heading2"]))
    story.append(Paragraph(f"Occupation Summary: {json.dumps(persona_summary.get('occupation_summary', {}), indent=2)}", styles["BodyText"]))
    story.append(Paragraph(f"Top Goals: {', '.join(persona_summary.get('top_goals', [])) or 'N/A'}", styles["BodyText"]))
    story.append(Paragraph(f"Top Pain Points: {', '.join(persona_summary.get('top_pain_points', [])) or 'N/A'}", styles["BodyText"]))
    story.append(Paragraph(f"Buying Behaviour: {', '.join(persona_summary.get('buying_behaviour', [])) or 'N/A'}", styles["BodyText"]))
    story.append(Paragraph(f"Technology Usage: {', '.join(persona_summary.get('technology_usage', [])) or 'N/A'}", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Product Fit Analysis", styles["Heading2"]))
    story.append(Paragraph(f"Overall Score: {fit_analysis.get('overall_score', 0)}", styles["BodyText"]))
    for insight in fit_analysis.get("key_insights", []):
        story.append(Paragraph(f"- {insight.get('question', '')}: {insight.get('readable_summary', insight.get('insight', ''))}", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Key Insights", styles["Heading2"]))
    for item in key_insights:
        story.append(Paragraph(f"- {item}", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Final Recommendation", styles["Heading2"]))
    story.append(Paragraph(str(final_recommendation), styles["BodyText"]))
    doc.build(story)
    return buffer.getvalue()


def generate_demo_dataset(
    product_name: str = "FitPulse AI",
    research_goal: str = "Understand retention barriers and product adoption intent.",
) -> Dict[str, Any]:
    """Create a realistic demo dataset without requiring Gemini or external APIs."""
    personas = [
        {
            "id": "demo-1",
            "name": "Aarav Sharma",
            "age": "26",
            "gender": "Male",
            "occupation": "Software Engineer",
            "education": "Bachelor's Degree",
            "income": "$75k",
            "company": "Tech Startup",
            "goals": ["Improve productivity", "Stay healthy", "Learn new tools"],
            "pain_points": ["Time pressure", "Low motivation", "Incomplete routines"],
            "traits": ["Driven", "Curious", "Tech-savvy"],
            "behaviour": ["Uses mobile apps daily", "Prefers automation", "Likes short sessions"],
            "technology_usage": "High",
            "buying_behaviour": "Value-driven and mobile-first",
            "psychological_profile": "Motivated by clear outcomes and efficiency",
            "behavior_pattern": "Prefers quick, measurable progress",
            "big_five": {"openness": 85, "conscientiousness": 72, "extraversion": 60, "agreeableness": 63, "neuroticism": 30},
        },
        {
            "id": "demo-2",
            "name": "Meera Patel",
            "age": "29",
            "gender": "Female",
            "occupation": "Student",
            "education": "Graduate Student",
            "income": "$35k",
            "company": "University",
            "goals": ["Build discipline", "Stay consistent", "Manage stress"],
            "pain_points": ["Overwhelm", "Poor routine structure", "Busy schedule"],
            "traits": ["Ambitious", "Adaptive", "Resilient"],
            "behaviour": ["Uses mobile-first tools", "Responds to social proof", "Likes simple guidance"],
            "technology_usage": "Medium-High",
            "buying_behaviour": "Affordable and simple",
            "psychological_profile": "Responsive to motivation and social encouragement",
            "behavior_pattern": "Wants quick wins and guided routines",
            "big_five": {"openness": 78, "conscientiousness": 68, "extraversion": 58, "agreeableness": 80, "neuroticism": 42},
        },
        {
            "id": "demo-3",
            "name": "Lucas Reed",
            "age": "41",
            "gender": "Male",
            "occupation": "Operations Manager",
            "education": "MBA",
            "income": "$110k",
            "company": "Retail Chain",
            "goals": ["Reduce team friction", "Drive productivity", "Improve retention"],
            "pain_points": ["Manual tracking", "Lack of insight", "Operational delays"],
            "traits": ["Structured", "Analytical", "Goal-oriented"],
            "behaviour": ["Works across dashboards", "Values analytics", "Prefers reliable systems"],
            "technology_usage": "High",
            "buying_behaviour": "Trust-based and ROI focused",
            "psychological_profile": "Values measurable business outcomes",
            "behavior_pattern": "Prefers systems that reduce operational friction",
            "big_five": {"openness": 70, "conscientiousness": 85, "extraversion": 55, "agreeableness": 67, "neuroticism": 25},
        },
        {
            "id": "demo-4",
            "name": "Sofia Nair",
            "age": "34",
            "gender": "Female",
            "occupation": "Healthcare Professional",
            "education": "RN",
            "income": "$82k",
            "company": "Private Clinic",
            "goals": ["Improve wellness", "Stay organized", "Reduce stress"],
            "pain_points": ["Long shifts", "No time for planning", "Low energy"],
            "traits": ["Compassionate", "Focused", "Reliable"],
            "behaviour": ["Prefers mobile nudges", "Trusts evidence-based products", "Values flexibility"],
            "technology_usage": "Medium",
            "buying_behaviour": "Trust-centered and pragmatic",
            "psychological_profile": "Seeks balance and practical support",
            "behavior_pattern": "Prefers short, relevant interactions",
            "big_five": {"openness": 74, "conscientiousness": 76, "extraversion": 49, "agreeableness": 84, "neuroticism": 35},
        },
    ]

    survey_result = execute_survey(personas, product_name=product_name, research_goal=research_goal)
    report = build_research_report(personas, survey_result["responses"], product_name=product_name, research_goal=research_goal)

    return {
        "personas": personas,
        "survey_results": survey_result,
        "research_report": report,
    }
