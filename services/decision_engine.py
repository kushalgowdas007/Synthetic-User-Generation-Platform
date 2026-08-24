from __future__ import annotations

import uuid
from typing import Any, Dict, List, Mapping, Optional, Sequence
from models.schemas import ProductAction, StructuredInsight


def calculate_priority_score(
    impact: int,
    confidence: int,
    evidence_strength: int,
    affected_users_score: int,
    urgency: int,
    effort: int
) -> int:
    """
    Transparent priority calculation formula:
    Priority = round(
        0.25 * Impact +
        0.25 * Confidence +
        0.20 * Evidence Strength +
        0.15 * Affected Users +
        0.15 * (100 - Effort)
    )
    """
    impact_clamped = max(0, min(100, impact))
    confidence_clamped = max(0, min(100, confidence))
    evidence_clamped = max(0, min(100, evidence_strength))
    affected_clamped = max(0, min(100, affected_users_score))
    effort_clamped = max(0, min(100, effort))
    
    score = (
        (0.25 * impact_clamped) +
        (0.25 * confidence_clamped) +
        (0.20 * evidence_clamped) +
        (0.15 * affected_clamped) +
        (0.15 * (100 - effort_clamped))
    )
    return max(0, min(100, round(score)))


def generate_product_actions(
    insights_data: Optional[Mapping[str, Any]],
    personas: Sequence[Mapping[str, Any]],
    experiment: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    """
    Convert research insights and experiment context into prioritized ProductAction decision recommendations.
    """
    actions: List[ProductAction] = []
    
    if not insights_data:
        # Fallback default decisions if insights haven't been extracted yet
        default_actions = [
            ProductAction(
                id="act_default_1",
                title="Streamline Onboarding & Trust Signals",
                problem="New users require clear proof of value before committing.",
                recommendation="Add guided tooltips and a zero-risk 14-day free trial on landing.",
                impact=85,
                effort=35,
                confidence=80,
                evidence_strength=75,
                affected_users_score=85,
                urgency=80,
                priority=calculate_priority_score(85, 80, 75, 85, 80, 35),
                affected_personas=[str(p.get("name")) for p in personas[:3]],
                expected_outcomes=["Reduce drop-off by 25%", "Increase trial conversion"],
                source_insights=["Default setup"],
                status="Recommended"
            ),
            ProductAction(
                id="act_default_2",
                title="Transparent Pricing & Value Proof",
                problem="Uncertainty regarding hidden subscription costs.",
                recommendation="Publish tier comparison table with ROI calculator.",
                impact=80,
                effort=30,
                confidence=85,
                evidence_strength=80,
                affected_users_score=75,
                urgency=75,
                priority=calculate_priority_score(80, 85, 80, 75, 75, 30),
                affected_personas=[str(p.get("name")) for p in personas[:2]],
                expected_outcomes=["Increase paid conversion", "Reduce pricing friction"],
                source_insights=["Default setup"],
                status="Recommended"
            )
        ]
        return [act.to_dict() for act in default_actions]

    structured = insights_data.get("structured_insights", [])
    
    # 1. Action from Pain Points
    pain_points = insights_data.get("pain_points", [])
    for idx, pain_item in enumerate(pain_points[:3], 1):
        pain_name = str(pain_item.get("pain_point", "User Friction"))
        count = int(pain_item.get("count", 1))
        conf = int(pain_item.get("confidence_score", 80))
        
        impact = min(95, 60 + count * 8)
        effort = 40
        evidence_str = min(98, 55 + count * 12)
        affected_score = min(100, round((count / max(1, len(personas))) * 100))
        
        priority = calculate_priority_score(impact, conf, evidence_str, affected_score, 75, effort)
        
        actions.append(
            ProductAction(
                id=f"act_pain_{idx}",
                title=f"Resolve Friction: {pain_name.title()}",
                problem=f"{count} persona mentions highlight '{pain_name}' as a primary adoption hurdle.",
                recommendation=f"Redesign workflow and UX elements specifically addressing '{pain_name}'.",
                impact=impact,
                effort=effort,
                confidence=conf,
                evidence_strength=evidence_str,
                affected_users_score=affected_score,
                urgency=80,
                priority=priority,
                affected_personas=[str(p.get("name")) for p in personas if pain_name in str(p.get("pain_points", ""))],
                expected_outcomes=[f"Eliminate {pain_name} friction", "Improve core user retention"],
                source_insights=[f"Pain Point: {pain_name}"],
                status="Recommended"
            )
        )

    # 2. Action from Feature Requests
    features = insights_data.get("feature_requests", [])
    for idx, feat_item in enumerate(features[:2], 1):
        feat_name = str(feat_item.get("feature", "Core Feature"))
        count = int(feat_item.get("count", 1))
        conf = int(feat_item.get("confidence_score", 75))
        
        impact = 80
        effort = 50
        evidence_str = min(95, 50 + count * 10)
        affected_score = 70
        
        priority = calculate_priority_score(impact, conf, evidence_str, affected_score, 65, effort)
        
        actions.append(
            ProductAction(
                id=f"act_feat_{idx}",
                title=f"Implement Feature: {feat_name}",
                problem=f"Personas requested {feat_name} capabilities to enhance daily utility.",
                recommendation=f"Build native {feat_name} integration into the core product dashboard.",
                impact=impact,
                effort=effort,
                confidence=conf,
                evidence_strength=evidence_str,
                affected_users_score=affected_score,
                urgency=65,
                priority=priority,
                affected_personas=[str(p.get("name")) for p in personas[:2]],
                expected_outcomes=[f"Fulfill high-demand {feat_name} request", "Boost product engagement"],
                source_insights=[f"Feature Request: {feat_name}"],
                status="Recommended"
            )
        )

    # Sort actions by priority descending
    actions_sorted = sorted(actions, key=lambda a: a.priority, reverse=True)
    return [act.to_dict() for act in actions_sorted]
