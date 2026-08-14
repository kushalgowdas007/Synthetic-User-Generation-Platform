"""Deterministic research-brief copilot used online and in demo mode."""
from __future__ import annotations

from typing import Any, Dict, Mapping


def build_research_plan(brief: Mapping[str, Any]) -> Dict[str, Any]:
    product = str(brief.get("product_name") or "the product").strip()
    audience = str(brief.get("audience") or brief.get("target_audience") or "target users").strip()
    goal = str(brief.get("goals") or brief.get("research_objective") or "validate product-market fit").strip()
    industry = str(brief.get("industry") or "the market").strip()
    return {
        "research_objectives": [f"Understand the highest-value jobs {audience} expect {product} to solve.", f"Validate adoption barriers, willingness to pay, and trust signals for {product}.", f"Prioritize the smallest experience changes that advance: {goal}."],
        "research_hypothesis": f"{audience.title()} will adopt {product} when its value is concrete, onboarding is low-friction, and the trade-off against existing {industry} alternatives is clear.",
        "research_questions": ["Which problem feels most urgent today?", "What would make a user switch from their current workaround?", "What evidence is needed before trying or paying?"],
        "survey_questions": ["How likely are you to try this product?", "Which outcome would be most valuable?", "What would stop you from adopting it?", "What price or value exchange feels fair?"],
        "interview_questions": ["Tell me about the last time this problem slowed you down.", "Walk me through how you decide whether a new tool is trustworthy.", "What would make this feel indispensable after the first week?"],
        "success_metrics": ["Product-fit score ≥ 70/100", "At least 60% high adoption intent", "Top onboarding concern resolved in prototype"],
        "kpis": ["Adoption intent", "Trust confidence", "Time-to-first-value", "Willingness to pay"],
        "target_segments": [f"Primary: {audience}", "Pragmatic evaluators who compare value before switching", "Early adopters seeking a measurable workflow improvement"],
        "validation_strategy": ["Generate a diverse persona panel", "Run template survey and follow-up interviews", "Stress-test themes in a moderated focus group", "Use the insight and consultant reports to decide next experiment"],
        "competitor_analysis_plan": ["List 3 direct and 2 indirect alternatives", "Compare onboarding, trust signals, pricing, and core workflow", "Identify a defensible feature gap and test it with personas"],
    }
