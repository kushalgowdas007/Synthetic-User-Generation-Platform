from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from services.cache_service import compute_insight_signature, insight_cache
from services.telemetry import time_stage

THEME_KEYWORDS = {
    "Trust": ["trust", "reliable", "proof", "confidence", "safe", "evidence", "privacy"],
    "Pricing": ["price", "cost", "affordable", "pricing", "value", "pay", "trial", "subscription"],
    "Convenience": ["time", "quick", "easy", "simple", "friction", "convenience", "speed"],
    "Onboarding": ["onboarding", "guided", "setup", "learn", "steps", "first", "tutorial"],
    "Productivity": ["productive", "efficiency", "progress", "save time", "workflow", "automate"],
    "Risk": ["risk", "hesitation", "concern", "cautious", "unclear", "barrier", "doubt"],
    "Personalization": ["personal", "custom", "recommendation", "tailored", "relevant"],
    "Integration": ["integration", "connect", "workflow", "tools", "sync", "export"],
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
    "security",
]

STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "would", "from", "they", "their",
    "have", "need", "product", "persona", "because", "score", "current", "clear",
    "which", "what", "when", "where", "were", "been", "there", "will", "about",
}


@dataclass
class EvidencePoint:
    source_type: str  # "survey", "interview", "focus_group", "persona_profile"
    source_detail: str  # e.g., "Survey Q2: Adoption Likelihood"
    metric_or_quote: str  # e.g., "75% negative/neutral responses (3/4 personas)"
    affected_personas: List[str] = field(default_factory=list)
    confidence: int = 80

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredInsight:
    title: str
    type: str  # "Theme", "Pain Point", "Opportunity", "Contradiction", "Risk", "Positive Signal", "Behavioral Pattern", "Segment Difference"
    severity_or_importance: int  # 0-100
    confidence: int  # 0-100
    affected_personas_count: int
    affected_personas: List[str]
    evidence: List[EvidencePoint] = field(default_factory=list)
    source: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["evidence"] = [e.to_dict() if isinstance(e, EvidencePoint) else e for e in self.evidence]
        return res


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
        if row.get("role") in ("persona", "participant"):
            texts.append(
                {
                    "persona_name": str(row.get("persona_name", row.get("speaker", "Persona"))),
                    "source": "interview" if row.get("role") == "persona" else "focus_group",
                    "text": str(row.get("message", "")),
                }
            )
    return [item for item in texts if item["text"].strip()]


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def extract_research_insights(
    *,
    experiment: Mapping[str, Any],
    personas: Sequence[Mapping[str, Any]],
    survey_results: Mapping[str, Any] | None,
    interview_rows: Sequence[Mapping[str, Any]],
    focus_rows: Optional[Sequence[Mapping[str, Any]]] = None,
    bypass_cache: bool = False,
) -> Dict[str, Any]:
    """
    Extracts structured, evidence-traceable research insights clustered into 8 categories.
    Implements deterministic input signature caching to eliminate redundant recomputations.
    """
    focus_list = list(focus_rows or [])
    combined_conversation = [*interview_rows, *focus_list]
    
    # 1. Deterministic Insight Cache
    cache_key = compute_insight_signature(survey_results, interview_rows, focus_list, personas)
    if not bypass_cache:
        cached = insight_cache.get(cache_key)
        if cached:
            return cached

    with time_stage("insight_clustering"):
        text_items = _collect_text(survey_results, combined_conversation)
        texts = [item["text"] for item in text_items]
        combined = " ".join(texts).lower()
        total_texts = max(1, len(texts))
        total_personas = max(1, len(personas))
        all_persona_names = [str(p.get("name", "Persona")) for p in personas]

        # Theme analysis
        theme_counter: Counter[str] = Counter()
        theme_personas: defaultdict[str, set[str]] = defaultdict(set)
        for theme, keywords in THEME_KEYWORDS.items():
            for item in text_items:
                if any(kw in item["text"].lower() for kw in keywords):
                    theme_counter[theme] += 1
                    theme_personas[theme].add(item["persona_name"])

        # Survey aggregations & barriers
        pain_counter: Counter[str] = Counter()
        behavior_counter: Counter[str] = Counter()
        barrier_counter: Counter[str] = Counter()
        segment_map: defaultdict[str, List[str]] = defaultdict(list)
        early_adopters: List[Dict[str, Any]] = []

        survey_scores_by_persona: defaultdict[str, List[float]] = defaultdict(list)
        survey_responses = (survey_results or {}).get("responses", [])
        for response in survey_responses:
            if isinstance(response, Mapping):
                p_name = str(response.get("persona_name", "Persona"))
                score_val = float(response.get("score", 0) or 0)
                survey_scores_by_persona[p_name].append(score_val)
                fit_details = response.get("product_fit_details", {})
                if isinstance(fit_details, Mapping):
                    for weakness in fit_details.get("weaknesses", []):
                        barrier_counter[str(weakness)] += 1

        for persona in personas:
            persona_name = str(persona.get("name", "Persona"))
            tech = str(persona.get("technology_usage", "Medium"))
            segment_map[tech].append(persona_name)
            for pain in _as_list(persona.get("pain_points")):
                pain_counter[pain] += 1
                for theme, keywords in THEME_KEYWORDS.items():
                    if any(keyword in pain.lower() for keyword in keywords):
                        theme_counter[theme] += 1
                        theme_personas[theme].add(persona_name)
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
            if adopter_score >= 65:
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
            for response in survey_responses
            if isinstance(response, Mapping)
        ]
        product_fit = round(_mean(survey_scores), 2) if survey_scores else 60.0
        sentiment_counts = _sentiment_counts(survey_scores, combined_conversation)
        sentiment = max(sentiment_counts.items(), key=lambda item: item[1])[0] if sentiment_counts else _sentiment_from_score(product_fit)
        recommendation_score = _recommendation_score(survey_results, combined_conversation, product_fit)

        # -------------------------------------------------------------
        # 8 STRUCTURED INSIGHT CLUSTERS WITH EVIDENCE TRACEABILITY
        # -------------------------------------------------------------
        structured_clusters: Dict[str, List[Dict[str, Any]]] = {
            "themes": [],
            "pain_points": [],
            "opportunities": [],
            "contradictions": [],
            "risks": [],
            "positive_signals": [],
            "behavioral_patterns": [],
            "segment_differences": [],
        }

        # 1. Themes
        for theme, count in theme_counter.most_common(6):
            if count == 0:
                continue
            aff_p = list(theme_personas.get(theme, []))
            ev = [
                EvidencePoint(
                    source_type="interview/survey",
                    source_detail=f"Mentioned {count} times across responses",
                    metric_or_quote=f"Identified by {len(aff_p)}/{total_personas} synthetic personas",
                    affected_personas=aff_p,
                    confidence=_confidence(count, total_texts),
                )
            ]
            structured_clusters["themes"].append(
                StructuredInsight(
                    title=f"Core Theme: {theme}",
                    type="Theme",
                    severity_or_importance=min(100, 50 + count * 6),
                    confidence=_confidence(count, total_texts),
                    affected_personas_count=len(aff_p),
                    affected_personas=aff_p,
                    evidence=ev,
                    source=["survey", "interview"],
                    recommendation=f"Focus product messaging and onboarding design around {theme.lower()} guarantees.",
                ).to_dict()
            )

        # 2. Pain Points
        for pain, count in pain_counter.most_common(5):
            aff_p = [p for p in all_persona_names if pain in _as_list(personas[all_persona_names.index(p)].get("pain_points"))]
            ev = [
                EvidencePoint(
                    source_type="persona_profile/survey",
                    source_detail=f"Directly stated as top friction point",
                    metric_or_quote=f"Affects {len(aff_p)}/{total_personas} personas ({len(aff_p)/total_personas*100:.0f}%)",
                    affected_personas=aff_p,
                    confidence=_confidence(count, total_personas, base=70),
                )
            ]
            structured_clusters["pain_points"].append(
                StructuredInsight(
                    title=pain,
                    type="Pain Point",
                    severity_or_importance=min(100, 65 + count * 8),
                    confidence=_confidence(count, total_personas, base=70),
                    affected_personas_count=len(aff_p),
                    affected_personas=aff_p,
                    evidence=ev,
                    source=["survey", "persona_profile"],
                    recommendation=f"Prioritize product workflow adjustments to eliminate {pain.lower()}.",
                ).to_dict()
            )

        # 3. Opportunities
        for feature, count in feature_counter.most_common(4):
            structured_clusters["opportunities"].append(
                StructuredInsight(
                    title=f"High-Demand Capability: {feature}",
                    type="Opportunity",
                    severity_or_importance=min(100, 60 + count * 8),
                    confidence=_confidence(count, total_texts, base=65),
                    affected_personas_count=min(total_personas, count),
                    affected_personas=all_persona_names[:count],
                    evidence=[
                        EvidencePoint(
                            source_type="interview/conversation",
                            source_detail="Keyword extraction in feature discussions",
                            metric_or_quote=f"Requested {count} times across qualitative sessions",
                            affected_personas=all_persona_names[:count],
                            confidence=_confidence(count, total_texts, base=65),
                        )
                    ],
                    source=["interview", "focus_group"],
                    recommendation=f"Consider {feature} as a core differentiator in upcoming sprint roadmaps.",
                ).to_dict()
            )

        # 4. Contradictions
        # Check if high price sensitivity contradicts willingness to try
        if theme_counter.get("Pricing", 0) > 0 and theme_counter.get("Convenience", 0) > 0:
            structured_clusters["contradictions"].append(
                StructuredInsight(
                    title="Price Sensitivity vs. High Demand for Convenience",
                    type="Contradiction",
                    severity_or_importance=78,
                    confidence=82,
                    affected_personas_count=total_personas,
                    affected_personas=all_persona_names,
                    evidence=[
                        EvidencePoint(
                            source_type="survey/interview",
                            source_detail="Cross-theme contradiction audit",
                            metric_or_quote="Users demand high-touch convenience but express hesitation over paid tiers",
                            affected_personas=all_persona_names,
                            confidence=82,
                        )
                    ],
                    source=["survey", "interview"],
                    recommendation="Bridge the gap with a tiered pricing model anchored on measurable time savings.",
                ).to_dict()
            )

        # 5. Risks
        risks_text = []
        if product_fit < 60:
            structured_clusters["risks"].append(
                StructuredInsight(
                    title="Product-Fit Validation Threshold Warning",
                    type="Risk",
                    severity_or_importance=85,
                    confidence=88,
                    affected_personas_count=total_personas,
                    affected_personas=all_persona_names,
                    evidence=[
                        EvidencePoint(
                            source_type="survey",
                            source_detail="Overall Product Fit Metric",
                            metric_or_quote=f"Overall product-fit score is {product_fit:.1f}/100 (below 60.0 target)",
                            affected_personas=all_persona_names,
                            confidence=88,
                        )
                    ],
                    source=["survey"],
                    recommendation="Refine core value proposition and onboarding clarity before scaling customer acquisition.",
                ).to_dict()
            )
            risks_text.append("Current product-fit score is below the launch validation threshold.")

        for theme in ("Pricing", "Trust", "Risk", "Onboarding"):
            if theme_counter[theme] > 0:
                risks_text.append(f"{theme} is a recurring adoption barrier identified in research.")

        # 6. Positive Signals
        if sentiment == "positive" or product_fit >= 60:
            structured_clusters["positive_signals"].append(
                StructuredInsight(
                    title="Strong Baseline Product Concept Appeal",
                    type="Positive Signal",
                    severity_or_importance=round(product_fit),
                    confidence=84,
                    affected_personas_count=len(early_adopters) or 1,
                    affected_personas=[ea["persona"] for ea in early_adopters] or all_persona_names[:1],
                    evidence=[
                        EvidencePoint(
                            source_type="survey",
                            source_detail="Survey Sentiment & Early Adopter Identification",
                            metric_or_quote=f"{len(early_adopters)} persona(s) identified as high-affinity early adopters",
                            affected_personas=[ea["persona"] for ea in early_adopters] or all_persona_names[:1],
                            confidence=84,
                        )
                    ],
                    source=["survey", "interview"],
                    recommendation="Leverage early adopter personas for initial beta testing and case studies.",
                ).to_dict()
            )

        # 7. Behavioral Patterns
        for pattern, count in behavior_counter.most_common(4):
            structured_clusters["behavioral_patterns"].append(
                StructuredInsight(
                    title=pattern,
                    type="Behavioral Pattern",
                    severity_or_importance=70,
                    confidence=80,
                    affected_personas_count=count,
                    affected_personas=all_persona_names[:count],
                    evidence=[
                        EvidencePoint(
                            source_type="persona_profile",
                            source_detail="Behavior Pattern Analysis",
                            metric_or_quote=f"Observed across {count}/{total_personas} persona profiles",
                            affected_personas=all_persona_names[:count],
                            confidence=80,
                        )
                    ],
                    source=["persona_profile"],
                    recommendation="Align product workflow and notifications to match this behavioral routine.",
                ).to_dict()
            )

        # 8. Segment Differences
        for seg_name, p_names in segment_map.items():
            structured_clusters["segment_differences"].append(
                StructuredInsight(
                    title=f"Segment: {seg_name} ({len(p_names)} personas)",
                    type="Segment Difference",
                    severity_or_importance=65,
                    confidence=85,
                    affected_personas_count=len(p_names),
                    affected_personas=p_names,
                    evidence=[
                        EvidencePoint(
                            source_type="persona_profile",
                            source_detail="Technology Adoption Segmentation",
                            metric_or_quote=f"Represents {len(p_names)}/{total_personas} ({len(p_names)/total_personas*100:.0f}%) of cohort",
                            affected_personas=p_names,
                            confidence=85,
                        )
                    ],
                    source=["persona_profile"],
                    recommendation=f"Tailor onboarding depth and default settings specifically for the {seg_name} cohort.",
                ).to_dict()
            )

        top_quotes = _top_quotes(text_items, survey_results, combined_conversation)
        final_recommendations = _recommendations(theme_counter, barrier_counter, product_fit, recommendation_score)
        executive_summary = _summarize_feedback(theme_counter, product_fit)

        payload = {
            "product_name": experiment.get("product_name", ""),
            "themes": [
                {"theme": theme, "count": count, "confidence_score": _confidence(count, total_texts)}
                for theme, count in theme_counter.most_common() if count > 0
            ],
            "keywords": [
                {"keyword": kw, "count": cnt, "confidence_score": _confidence(cnt, total_texts)}
                for kw, cnt in keyword_counter.most_common(18)
            ],
            "pain_points": [
                {"pain_point": p, "count": cnt, "confidence_score": _confidence(cnt, total_personas)}
                for p, cnt in pain_counter.most_common(10)
            ],
            "feature_requests": [
                {"feature": f, "count": cnt, "confidence_score": _confidence(cnt, total_texts)}
                for f, cnt in feature_counter.most_common(10)
            ],
            "sentiment": sentiment,
            "sentiment_distribution": {
                k: {"count": v, "confidence_score": _confidence(v, max(1, sum(sentiment_counts.values())))}
                for k, v in sentiment_counts.items()
            },
            "product_fit_score": product_fit,
            "product_fit_confidence_score": _confidence(len(survey_scores), max(1, total_personas * 3), base=58),
            "recommendation_score": recommendation_score,
            "recommendation_confidence_score": _confidence(len(survey_scores) + len(combined_conversation), total_texts, base=58),
            "early_adopter_detection": sorted(early_adopters, key=lambda x: x["score"], reverse=True),
            "persona_segmentation": {k: {"personas": v, "count": len(v)} for k, v in segment_map.items()},
            "top_quotes": top_quotes,
            "final_ai_recommendations": final_recommendations,
            "recommendations": [item["recommendation"] for item in final_recommendations],
            "product_feedback": executive_summary,
            "executive_summary": executive_summary,
            "structured_clusters": structured_clusters,
            "risk_analysis": risks_text or ["No material risk signal was detected in the available responses."],
            "confidence_score": min(100, round(35 + min(len(texts), 30) * 2 + min(sum(theme_counter.values()), 20) * 1.5, 1)),
            "response_count": len(survey_responses),
            "interview_message_count": len(combined_conversation),
        }

        # Cache extracted insights
        insight_cache.set(cache_key, payload)
        return payload


def _sentiment_counts(scores: Sequence[float], interview_rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter(_sentiment_from_score(score) for score in scores)
    for row in interview_rows:
        if row.get("role") not in ("persona", "participant"):
            continue
        emotion = str(row.get("emotional_state", "")).lower()
        message = str(row.get("message", "")).lower()
        if emotion in {"curious", "confident"} or any(term in message for term in ("try", "seriously", "recommend", "love")):
            counter["positive"] += 1
        elif emotion in {"concerned", "cautious"} or any(term in message for term in ("risk", "concern", "unclear", "hate", "refuse")):
            counter["negative"] += 1
        else:
            counter["neutral"] += 1
    if not counter:
        counter["neutral"] = 1
    return counter


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
        if row.get("role") in ("persona", "participant") and any(term in str(row.get("message", "")).lower() for term in ("recommend", "try", "value"))
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
        if row.get("role") in ("persona", "participant") and message:
            quotes.append(
                {
                    "persona_name": row.get("persona_name", row.get("speaker", "Persona")),
                    "quote": message,
                    "source": "interview" if row.get("role") == "persona" else "focus_group",
                    "confidence_score": 88,
                }
            )
    return quotes[:8]


def _recommendations(
    theme_counter: Counter[str],
    barrier_counter: Counter[str],
    product_fit: float,
    recommendation_score: float,
) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if theme_counter.get("Onboarding", 0) > 0 or barrier_counter:
        recs.append({
            "recommendation": "Streamline first-time user onboarding with guided walkthroughs to minimize friction.",
            "confidence_score": 90,
        })
    if theme_counter.get("Trust", 0) > 0 or theme_counter.get("Pricing", 0) > 0:
        recs.append({
            "recommendation": "Provide transparent pricing, clear security badges, and low-barrier trial tiers.",
            "confidence_score": 88,
        })
    if product_fit >= 70:
        recs.append({
            "recommendation": "Leverage enthusiastic early adopters for initial referral loops and case studies.",
            "confidence_score": 85,
        })
    else:
        recs.append({
            "recommendation": "Refine core value narrative and eliminate top usability barriers before broad launch.",
            "confidence_score": 82,
        })
    return recs


def _summarize_feedback(theme_counter: Counter[str], product_fit: float) -> str:
    top_themes = [theme for theme, count in theme_counter.most_common(2) if count > 0]
    theme_summary = f" Focus areas: {', '.join(top_themes)}." if top_themes else ""
    if product_fit >= 75:
        return f"High validation signal ({product_fit:.0f}/100). Cohort shows strong product-market fit and willingness to adopt.{theme_summary}"
    if product_fit >= 50:
        return f"Moderate validation signal ({product_fit:.0f}/100). Promising interest, but conversion depends on resolving adoption friction.{theme_summary}"
    return f"Cautionary validation signal ({product_fit:.0f}/100). Personas identified substantial pricing, trust, or workflow barriers.{theme_summary}"
