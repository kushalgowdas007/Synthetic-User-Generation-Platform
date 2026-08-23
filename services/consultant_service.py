from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from services.action_engine import ActionEngine


def build_consultant_report(
    experiment: Mapping[str, Any],
    insights: Mapping[str, Any] | None,
    survey: Mapping[str, Any] | None,
    focus_group: Sequence[Mapping[str, Any]],
    personas: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Generates an executive-level launch readiness and product strategy recommendation with prioritized decisions."""
    fit = float((insights or {}).get("product_fit_score") or (survey or {}).get("product_fit_score") or 60.0)
    persona_list = list(personas or [])
    
    # Calculate launch readiness
    has_insights = bool(insights)
    has_focus = bool(focus_group)
    readiness = round(min(95, max(20, fit * 0.70 + (14 if has_focus else 0) + (10 if has_insights else 0))))

    # Decisions from Action Engine
    decisions = ActionEngine.generate_decisions(
        experiment=experiment,
        personas=persona_list,
        insights=insights,
        survey_results=survey,
    )
    top_3_decisions = ActionEngine.get_top_decisions(decisions, limit=3)

    risks = [
        "Clarify pricing tiers and ROI proof points before scaling acquisition.",
        "Test guided onboarding with non-technical cohorts to avoid early churn.",
    ]
    if fit >= 70:
        risks = [
            "Protect product simplicity while expanding roadmap integrations.",
            "Segment willingness-to-pay across early-adopter vs mainstream personas.",
        ]

    return {
        "launch_readiness": readiness,
        "market_fit": round(fit),
        "revenue_potential": "High" if fit >= 70 else "Promising" if fit >= 48 else "Unproven",
        "risk_score": max(5, 100 - readiness),
        "pricing_recommendation": "Offer a transparent 14-day trial and tier pricing by measurable outcome/usage.",
        "customer_segment": "Pragmatic, outcome-focused users who need clear trust signals before switching.",
        "feature_priorities": [
            "Guided 3-step first-use setup wizard",
            "Transparent trust and privacy evidence layer",
            "Automated summary and report export triggers",
        ],
        "business_recommendations": [
            "Lead acquisition with time-saved metrics rather than technical feature lists.",
            "Address persona objections as transparent proof points on landing pages.",
            "Run an outcome-based pricing pilot with identified early-adopter personas.",
        ],
        "roadmap": [
            "Now (Weeks 1-2): Streamline onboarding & eliminate setup friction",
            "Next (Weeks 3-5): Deploy ROI proof calculator & low-risk trial tiers",
            "Later (Weeks 6-8): Expand automated summary connectors & team workflows",
        ],
        "swot": {
            "strengths": ["Evidence-based research workflow", "Rapid persona-driven iteration cycles"],
            "weaknesses": ["Synthetic findings require continuous human sample validation"],
            "opportunities": ["Capture high-intent early adopters with focused time-saving workflows"],
            "threats": risks,
        },
        "why": (
            f"Readiness score of {readiness}% is derived from a {fit:.0f}/100 product-fit signal, "
            f"{'triangulated focus-group discourse' if has_focus else 'pending focus-group input'}, "
            f"and evidence-weighted prioritization across {len(persona_list)} synthetic personas."
        ),
        "decisions": decisions,
        "top_decisions": top_3_decisions,
    }
