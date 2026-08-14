from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence


def build_consultant_report(experiment: Mapping[str, Any], insights: Mapping[str, Any] | None, survey: Mapping[str, Any] | None, focus_group: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    fit = float((insights or {}).get("would_use_product_score") or (survey or {}).get("product_fit_score") or 0)
    readiness = round(min(95, max(20, fit * .72 + (12 if focus_group else 0) + (8 if insights else 0))))
    risks = ["Clarify pricing and proof points before broad acquisition.", "Test onboarding with first-time users before launch."]
    if fit >= 70: risks = ["Protect product clarity while scaling acquisition.", "Validate willingness-to-pay by segment."]
    return {
        "launch_readiness": readiness, "market_fit": round(fit), "revenue_potential": "High" if fit >= 70 else "Promising" if fit >= 45 else "Unproven",
        "risk_score": 100 - readiness, "pricing_recommendation": "Offer a transparent trial and tier pricing by measurable outcome.",
        "customer_segment": "Pragmatic, time-constrained users who need confidence before switching.",
        "feature_priorities": ["Guided first-use experience", "Trust and evidence layer", "Fast path to a measurable outcome"],
        "business_recommendations": ["Lead messaging with the clearest outcome, not feature breadth.", "Use persona objections as landing-page proof points.", "Run a segmented pricing test after onboarding validation."],
        "roadmap": ["Now: resolve adoption friction", "Next: validate price/value narrative", "Later: expand winning workflow and integrations"],
        "swot": {"strengths": ["Evidence-led research workflow", "Fast persona-based iteration"], "weaknesses": ["Synthetic findings need validation with real users"], "opportunities": ["Own a sharp, trusted niche workflow"], "threats": risks},
        "why": f"Readiness is based on a {fit:.0f}/100 product-fit signal, available insight coverage, and {'focus-group triangulation' if focus_group else 'the need for focus-group triangulation'}."
    }
