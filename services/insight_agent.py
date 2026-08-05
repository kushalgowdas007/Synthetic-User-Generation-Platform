from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Mapping, Sequence


THEME_KEYWORDS = {
    "Trust": ["trust", "reliable", "proof", "confidence", "safe", "evidence"],
    "Pricing": ["price", "cost", "affordable", "pricing", "value", "pay", "trial"],
    "Convenience": ["time", "quick", "easy", "simple", "friction", "convenience"],
    "Onboarding": ["onboarding", "guided", "setup", "learn", "steps", "first"],
    "Productivity": ["productive", "efficiency", "progress", "save time", "workflow"],
    "Risk": ["risk", "hesitation", "concern", "cautious", "unclear", "barrier"],
    "Personalization": ["personal", "custom", "recommendation", "tailored"],
    "Integration": ["integration", "connect", "workflow", "tools", "sync"],
}

FEATURE_KEYWORDS = [
    "feature",
    "automation",
    "analytics",
    "personalization",
    "integration",
    "dashboard",
    "reminder",
    "export",
    "collaboration",
]

STOP_WORDS = {
    "the",
    "and",
    "for",
    "that",
    "this",
    "with",
    "would",
    "from",
    "they",
    "their",
    "have",
    "need",
    "product",
    "persona",
    "because",
    "score",
    "current",
    "clear",
}


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, Mapping):
        return [f"{key}: {item}" for key, item in value.items() if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _sentiment_from_score(score: float) -> str:
    if score >= 70:
        return "positive"
    if score >= 45:
        return "neutral"
    return "negative"


def _confidence(count: int, total: int, base: int = 62) -> int:
    if total <= 0:
        return base
    return max(45, min(98, round(base + (count / total) * 34)))


def _tokens(text: str) -> List[str]:
    return [
        token.lower()
        for token in re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", text)
        if token.lower() not in STOP_WORDS
    ]


def _collect_text(
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, str]]:
    texts: List[Dict[str, str]] = []
    if survey_results:
        for response in survey_results.get("responses", []):
            if isinstance(response, Mapping):
                persona = str(response.get("persona_name", "Persona"))
                texts.extend(
                    [
                        {"persona_name": persona, "source": "survey", "text": str(response.get("answer", ""))},
                        {"persona_name": persona, "source": "survey", "text": str(response.get("reasoning", ""))},
                        {"persona_name": persona, "source": "survey", "text": str(response.get("question", ""))},
                    ]
                )
    for row in interview_rows:
        if row.get("role") == "persona":
            texts.append(
                {
                    "persona_name": str(row.get("persona_name", "Persona")),
                    "source": "interview",
                    "text": str(row.get("message", "")),
                }
            )
    return [item for item in texts if item["text"].strip()]


def extract_research_insights(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    text_items = _collect_text(survey_results, interview_rows)
    texts = [item["text"] for item in text_items]
    combined = " ".join(texts).lower()
    total_texts = max(1, len(texts))

    theme_counter: Counter[str] = Counter()
    for theme, keywords in THEME_KEYWORDS.items():
        theme_counter[theme] = sum(combined.count(keyword) for keyword in keywords)

    pain_counter: Counter[str] = Counter()
    behavior_counter: Counter[str] = Counter()
    barrier_counter: Counter[str] = Counter()
    segment_map: defaultdict[str, List[str]] = defaultdict(list)
    early_adopters: List[Dict[str, Any]] = []

    survey_scores_by_persona: defaultdict[str, List[float]] = defaultdict(list)
    for response in (survey_results or {}).get("responses", []):
        if isinstance(response, Mapping):
            survey_scores_by_persona[str(response.get("persona_name", "Persona"))].append(float(response.get("score", 0) or 0))
            fit_details = response.get("product_fit_details", {})
            if isinstance(fit_details, Mapping):
                for weakness in fit_details.get("weaknesses", []):
                    barrier_counter[str(weakness)] += 1

    for persona in personas:
        persona_name = str(persona.get("name", "Persona"))
        tech = str(persona.get("technology_usage", "Unknown"))
        segment_map[tech].append(persona_name)
        for pain in _as_list(persona.get("pain_points")):
            pain_counter[pain] += 1
            for theme, keywords in THEME_KEYWORDS.items():
                if any(keyword in pain.lower() for keyword in keywords):
                    theme_counter[theme] += 1
                    barrier_counter[pain] += 1
        value = persona.get("behavior_pattern")
        if isinstance(value, Mapping):
            for item in value.values():
                behavior_counter[str(item)] += 1
        else:
            behavior_counter.update(_as_list(value))

        big_five = persona.get("big_five_personality") or persona.get("big_five") or {}
        openness = float(big_five.get("openness", 55) or 55) if isinstance(big_five, Mapping) else 55.0
        tech_bonus = 20 if any(term in tech.lower() for term in ("high", "advanced", "mobile")) else 6
        avg_survey_score = _mean(survey_scores_by_persona.get(persona_name, []))
        adopter_score = round((openness * 0.45) + (avg_survey_score * 0.40) + tech_bonus, 2)
        if adopter_score >= 68:
            early_adopters.append(
                {
                    "persona": persona_name,
                    "score": min(100, adopter_score),
                    "segment": tech,
                    "confidence_score": _confidence(1 + len(survey_scores_by_persona.get(persona_name, [])), total_texts),
                }
            )

    keyword_counter = Counter(_tokens(combined))
    feature_counter = Counter()
    for keyword in FEATURE_KEYWORDS:
        count = combined.count(keyword)
        if count:
            feature_counter[keyword.title()] = count

    survey_scores = [
        float(response.get("score", 0) or 0)
        for response in (survey_results or {}).get("responses", [])
        if isinstance(response, Mapping)
    ]
    product_fit = round(_mean(survey_scores), 2)
    recommendation_score = _recommendation_score(survey_results, interview_rows, product_fit)
    sentiment_counts = _sentiment_counts(survey_scores, interview_rows)
    sentiment = max(sentiment_counts.items(), key=lambda item: item[1])[0] if sentiment_counts else _sentiment_from_score(product_fit)

    top_quotes = _top_quotes(text_items, survey_results, interview_rows)
    final_recommendations = _recommendations(theme_counter, barrier_counter, product_fit, recommendation_score)

    themes = [
        {"theme": theme, "count": count, "confidence_score": _confidence(count, total_texts)}
        for theme, count in theme_counter.most_common()
        if count > 0
    ]

    return {
        "product_name": experiment.get("product_name", ""),
        "themes": themes,
        "keywords": [
            {"keyword": keyword, "count": count, "confidence_score": _confidence(count, total_texts)}
            for keyword, count in keyword_counter.most_common(18)
        ],
        "pain_points": [
            {"pain_point": pain, "count": count, "confidence_score": _confidence(count, max(1, len(personas)))}
            for pain, count in pain_counter.most_common(10)
        ],
        "feature_requests": [
            {"feature": feature, "count": count, "confidence_score": _confidence(count, total_texts)}
            for feature, count in feature_counter.most_common(10)
        ],
        "positive_sentiment": _sentiment_record("positive", sentiment_counts, total_texts),
        "neutral_sentiment": _sentiment_record("neutral", sentiment_counts, total_texts),
        "negative_sentiment": _sentiment_record("negative", sentiment_counts, total_texts),
        "sentiment_distribution": {
            key: {"count": value, "confidence_score": _confidence(value, max(1, sum(sentiment_counts.values())))}
            for key, value in sentiment_counts.items()
        },
        "sentiment": sentiment,
        "behavior_patterns": [
            {"pattern": pattern, "count": count, "confidence_score": _confidence(count, max(1, len(personas)))}
            for pattern, count in behavior_counter.most_common(10)
        ],
        "product_adoption_barriers": [
            {"barrier": barrier, "count": count, "confidence_score": _confidence(count, total_texts)}
            for barrier, count in barrier_counter.most_common(10)
        ],
        "product_fit_score": product_fit,
        "product_fit_confidence_score": _confidence(len(survey_scores), max(1, len(personas) * 3), base=58),
        "recommendation_score": recommendation_score,
        "recommendation_confidence_score": _confidence(len(survey_scores) + len(interview_rows), total_texts, base=58),
        "early_adopter_detection": sorted(early_adopters, key=lambda item: item["score"], reverse=True),
        "persona_segmentation": {
            segment: {"personas": names, "count": len(names), "confidence_score": _confidence(len(names), max(1, len(personas)))}
            for segment, names in segment_map.items()
        },
        "top_quotes": top_quotes,
        "final_ai_recommendations": final_recommendations,
        "recommendations": [item["recommendation"] for item in final_recommendations],
        "product_feedback": _summarize_feedback(theme_counter, product_fit),
        "would_use_product_score": recommendation_score,
        "response_count": len((survey_results or {}).get("responses", [])),
        "interview_message_count": len(interview_rows),
    }


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def _sentiment_counts(scores: Sequence[float], interview_rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter(_sentiment_from_score(score) for score in scores)
    for row in interview_rows:
        if row.get("role") != "persona":
            continue
        emotion = str(row.get("emotional_state", "")).lower()
        message = str(row.get("message", "")).lower()
        if emotion in {"curious", "confident"} or any(term in message for term in ("try", "seriously", "recommend")):
            counter["positive"] += 1
        elif emotion in {"concerned", "cautious"} or any(term in message for term in ("risk", "concern", "unclear")):
            counter["negative"] += 1
        else:
            counter["neutral"] += 1
    if not counter:
        counter["neutral"] = 1
    return counter


def _sentiment_record(label: str, counts: Counter[str], total_texts: int) -> Dict[str, Any]:
    count = counts.get(label, 0)
    return {
        "label": label,
        "count": count,
        "share": round((count / max(1, sum(counts.values()))) * 100, 2),
        "confidence_score": _confidence(count, total_texts),
    }


def _recommendation_score(
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    product_fit: float,
) -> float:
    recommend_scores = [
        float(response.get("score", 0) or 0)
        for response in (survey_results or {}).get("responses", [])
        if isinstance(response, Mapping)
        and "recommend" in str(response.get("question", "")).lower()
    ]
    if recommend_scores:
        return round(_mean(recommend_scores), 2)
    positive_interviews = sum(
        1
        for row in interview_rows
        if row.get("role") == "persona" and any(term in str(row.get("message", "")).lower() for term in ("recommend", "try", "value"))
    )
    interview_adjustment = min(12, positive_interviews * 2)
    return round(min(100, product_fit + interview_adjustment), 2)


def _top_quotes(
    text_items: Sequence[Mapping[str, str]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    quotes: List[Dict[str, Any]] = []
    for row in interview_rows:
        message = str(row.get("message", "")).strip()
        if row.get("role") == "persona" and message:
            quotes.append(
                {
                    "persona_name": row.get("persona_name", "Persona"),
                    "quote": message,
                    "source": "interview",
                    "confidence_score": 88,
                }
            )
    if not quotes and survey_results:
        for response in survey_results.get("responses", []):
            if isinstance(response, Mapping) and str(response.get("reasoning", "")).strip():
                quotes.append(
                    {
                        "persona_name": response.get("persona_name", "Persona"),
                        "quote": str(response.get("reasoning", "")),
                        "source": "survey",
                        "confidence_score": int(response.get("confidence_score", 72) or 72),
                    }
                )
    if not quotes:
        for item in text_items[:5]:
            quotes.append(
                {
                    "persona_name": item.get("persona_name", "Persona"),
                    "quote": item.get("text", ""),
                    "source": item.get("source", "research"),
                    "confidence_score": 68,
                }
            )
    return quotes[:8]


def _recommendations(
    theme_counter: Counter[str],
    barrier_counter: Counter[str],
    product_fit: float,
    recommendation_score: float,
) -> List[Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []
    if theme_counter["Pricing"] > 0:
        recommendations.append(
            {
                "recommendation": "Make pricing, trial terms, and ROI explicit early in the journey.",
                "confidence_score": _confidence(theme_counter["Pricing"], max(1, sum(theme_counter.values()))),
            }
        )
    if theme_counter["Trust"] > 0:
        recommendations.append(
            {
                "recommendation": "Add trust signals such as reviews, evidence, demos, and transparent claims.",
                "confidence_score": _confidence(theme_counter["Trust"], max(1, sum(theme_counter.values()))),
            }
        )
    if theme_counter["Convenience"] > 0 or theme_counter["Onboarding"] > 0:
        count = theme_counter["Convenience"] + theme_counter["Onboarding"]
        recommendations.append(
            {
                "recommendation": "Prioritize a low-friction onboarding path with guided first actions.",
                "confidence_score": _confidence(count, max(1, sum(theme_counter.values()))),
            }
        )
    if barrier_counter:
        top_barrier = barrier_counter.most_common(1)[0][0]
        recommendations.append(
            {
                "recommendation": f"Address the leading adoption barrier: {top_barrier}.",
                "confidence_score": _confidence(barrier_counter[top_barrier], max(1, sum(barrier_counter.values()))),
            }
        )
    if product_fit < 50 or recommendation_score < 50:
        recommendations.append(
            {
                "recommendation": "Reframe messaging around the strongest persona pain points before scaling acquisition.",
                "confidence_score": 82,
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "recommendation": "Maintain the current value proposition and validate with a larger persona set.",
                "confidence_score": 70,
            }
        )
    return recommendations[:8]


def _summarize_feedback(theme_counter: Counter[str], product_fit: float) -> str:
    top_theme = theme_counter.most_common(1)[0][0] if theme_counter else "Value"
    if product_fit >= 70:
        return f"Personas show strong product fit, with {top_theme.lower()} emerging as the main adoption lever."
    if product_fit >= 45:
        return f"Personas show moderate fit. {top_theme} needs clearer positioning to increase adoption intent."
    return f"Product fit is currently weak. Address {top_theme.lower()} and core pain points before launch."
