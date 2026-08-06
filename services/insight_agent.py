from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Mapping, Sequence


THEME_KEYWORDS = {
    "Trust": ["trust", "reliable", "proof", "confidence", "safe"],
    "Pricing": ["price", "cost", "affordable", "pricing", "value", "pay"],
    "Convenience": ["time", "quick", "easy", "simple", "friction", "convenience"],
    "Onboarding": ["onboarding", "guided", "setup", "learn", "steps"],
    "Productivity": ["productive", "efficiency", "progress", "save time", "workflow"],
    "Risk": ["risk", "hesitation", "concern", "cautious", "unclear"],
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


def _collect_text(survey_results: Mapping[str, Any] | None, interview_rows: Sequence[Mapping[str, Any]]) -> List[str]:
    texts: List[str] = []
    if survey_results:
        for response in survey_results.get("responses", []):
            if isinstance(response, Mapping):
                texts.extend(
                    [
                        str(response.get("answer", "")),
                        str(response.get("reasoning", "")),
                        str(response.get("question", "")),
                    ]
                )
    for row in interview_rows:
        if row.get("role") == "persona":
            texts.append(str(row.get("message", "")))
    return [text for text in texts if text.strip()]


def extract_research_insights(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    texts = _collect_text(survey_results, interview_rows)
    combined = " ".join(texts).lower()
    theme_counter: Counter[str] = Counter()
    for theme, keywords in THEME_KEYWORDS.items():
        theme_counter[theme] = sum(combined.count(keyword) for keyword in keywords)

    if not any(theme_counter.values()):
        for persona in personas:
            for pain in _as_list(persona.get("pain_points")):
                for theme, keywords in THEME_KEYWORDS.items():
                    if any(keyword in pain.lower() for keyword in keywords):
                        theme_counter[theme] += 1

    survey_scores = [
        float(response.get("score", 0) or 0)
        for response in (survey_results or {}).get("responses", [])
        if isinstance(response, Mapping)
    ]
    product_fit = round(sum(survey_scores) / len(survey_scores), 2) if survey_scores else 0.0
    sentiment = _sentiment_from_score(product_fit)

    segment_map: defaultdict[str, List[str]] = defaultdict(list)
    for persona in personas:
        tech = str(persona.get("technology_usage", "Unknown"))
        segment_map[tech].append(str(persona.get("name", "Persona")))

    top_quotes = [
        str(row.get("message", ""))
        for row in interview_rows
        if row.get("role") == "persona" and str(row.get("message", "")).strip()
    ][:5]
    if not top_quotes and survey_results:
        top_quotes = [
            str(response.get("reasoning", ""))
            for response in survey_results.get("responses", [])
            if isinstance(response, Mapping) and str(response.get("reasoning", "")).strip()
        ][:5]

    recommendations = []
    if theme_counter["Pricing"] > 0:
        recommendations.append("Make pricing, trial terms, and ROI explicit early in the journey.")
    if theme_counter["Trust"] > 0:
        recommendations.append("Add trust signals such as reviews, evidence, demos, and transparent claims.")
    if theme_counter["Convenience"] > 0 or theme_counter["Onboarding"] > 0:
        recommendations.append("Prioritize a low-friction onboarding path with guided first actions.")
    if product_fit < 50:
        recommendations.append("Reframe messaging around the strongest persona pain points before scaling acquisition.")
    if not recommendations:
        recommendations.append("Maintain the current value proposition and validate with a larger persona set.")

    tokens = [token for token in re.findall(r"[a-z]{4,}", combined) if token not in {"this", "that", "with", "from", "would", "product", "because", "response", "persona"}]
    keyword_frequency = [{"keyword": word, "count": count} for word, count in Counter(tokens).most_common(12)]
    topic_clusters = [
        {"topic": theme, "keywords": keywords, "mentions": theme_counter[theme]}
        for theme, keywords in THEME_KEYWORDS.items() if theme_counter[theme]
    ]
    risks = []
    for theme in ("Pricing", "Trust", "Risk", "Onboarding"):
        if theme_counter[theme]:
            risks.append(f"{theme} is a recurring adoption risk and should be addressed before launch.")
    if product_fit < 50:
        risks.append("The current product-fit score is below the validation threshold.")
    confidence = min(100, round(35 + min(len(texts), 30) * 2 + min(sum(theme_counter.values()), 20) * 1.5, 1))
    executive_summary = _summarize_feedback(theme_counter, product_fit)

    return {
        "product_name": experiment.get("product_name", ""),
        "themes": [{"theme": theme, "count": count} for theme, count in theme_counter.most_common() if count > 0],
        "sentiment": sentiment,
        "behavior_patterns": _top_persona_values(personas, "behavior_pattern"),
        "product_feedback": _summarize_feedback(theme_counter, product_fit),
        "recommendations": recommendations,
        "top_quotes": top_quotes,
        "would_use_product_score": product_fit,
        "persona_segmentation": dict(segment_map),
        "keyword_frequency": keyword_frequency,
        "topic_clusters": topic_clusters,
        "risk_analysis": risks or ["No material risk signal was detected in the available responses."],
        "confidence_score": confidence,
        "executive_summary": executive_summary,
        "response_count": len((survey_results or {}).get("responses", [])),
        "interview_message_count": len(interview_rows),
    }


def _top_persona_values(personas: Sequence[Mapping[str, Any]], key: str) -> List[str]:
    counter: Counter[str] = Counter()
    for persona in personas:
        value = persona.get(key)
        if isinstance(value, Mapping):
            for item in value.values():
                counter[str(item)] += 1
        else:
            counter.update(_as_list(value))
    return [item for item, _ in counter.most_common(5)]


def _summarize_feedback(theme_counter: Counter[str], product_fit: float) -> str:
    top_theme = theme_counter.most_common(1)[0][0] if theme_counter else "Value"
    if product_fit >= 70:
        return f"Personas show strong product fit, with {top_theme.lower()} emerging as the main adoption lever."
    if product_fit >= 45:
        return f"Personas show moderate fit. {top_theme} needs clearer positioning to increase adoption intent."
    return f"Product fit is currently weak. Address {top_theme.lower()} and core pain points before launch."
