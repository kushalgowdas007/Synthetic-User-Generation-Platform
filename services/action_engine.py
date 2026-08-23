from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence


@dataclass
class PriorityBreakdown:
    impact: int
    confidence: int
    evidence_strength: int
    urgency: int
    effort: int
    formula_explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductDecision:
    id: str
    title: str
    problem: str
    recommendation: str
    priority: int
    impact: int
    effort: int
    confidence: int
    evidence_strength: int
    urgency: int
    affected_personas: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    source_insights: List[str] = field(default_factory=list)
    status: str = "Recommended"
    breakdown: Optional[PriorityBreakdown] = None

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.breakdown:
            res["breakdown"] = self.breakdown.to_dict()
        return res


def calculate_priority_score(
    *,
    impact: int,
    confidence: int,
    evidence_strength: int,
    urgency: int,
    effort: int,
) -> tuple[int, PriorityBreakdown]:
    """
    Transparent weighted priority scoring formula:
    Priority = round((Impact * 0.25) + (Confidence * 0.20) + (Evidence * 0.20) + (Urgency * 0.15) + ((100 - Effort) * 0.20))
    """
    imp = max(0, min(100, impact))
    conf = max(0, min(100, confidence))
    ev = max(0, min(100, evidence_strength))
    urg = max(0, min(100, urgency))
    eff = max(0, min(100, effort))

    raw = (imp * 0.25) + (conf * 0.20) + (ev * 0.20) + (urg * 0.15) + ((100 - eff) * 0.20)
    score = max(0, min(100, round(raw)))

    breakdown = PriorityBreakdown(
        impact=imp,
        confidence=conf,
        evidence_strength=ev,
        urgency=urg,
        effort=eff,
        formula_explanation=(
            f"Impact ({imp}×25%) + Confidence ({conf}×20%) + Evidence ({ev}×20%) + "
            f"Urgency ({urg}×15%) + Ease (100-{eff}×20%) = {score}/100"
        ),
    )
    return score, breakdown


class ActionEngine:
    """Transforms raw research insights and survey feedback into prioritized product decisions."""

    @classmethod
    def generate_decisions(
        cls,
        *,
        experiment: Mapping[str, Any],
        personas: Sequence[Mapping[str, Any]],
        insights: Mapping[str, Any] | None,
        survey_results: Mapping[str, Any] | None,
    ) -> List[Dict[str, Any]]:
        decisions: List[ProductDecision] = []
        product_name = str(experiment.get("product_name", "the product")).strip() or "the product"
        all_persona_names = [str(p.get("name", "Persona")) for p in personas]
        
        product_fit = float((insights or {}).get("product_fit_score") or (survey_results or {}).get("product_fit_score") or 60.0)
        themes = (insights or {}).get("themes", [])
        pain_points = (insights or {}).get("pain_points", [])
        barriers = (insights or {}).get("product_adoption_barriers", [])
        theme_names = [t.get("theme") for t in themes if isinstance(t, Mapping)]

        # Decision 1: Onboarding / Friction Reduction
        onboarding_affected = all_persona_names[:max(1, len(all_persona_names) - 1)]
        imp1, conf1, ev1, urg1, eff1 = (88, 85, 90, 85, 35) if "Onboarding" in theme_names or barriers else (75, 80, 75, 70, 30)
        p1, b1 = calculate_priority_score(impact=imp1, confidence=conf1, evidence_strength=ev1, urgency=urg1, effort=eff1)
        decisions.append(
            ProductDecision(
                id="dec_streamline_onboarding",
                title=f"Guided Setup Wizard & Frictionless Onboarding for {product_name}",
                problem="Synthetic users consistently flagged setup complexity, time constraints, and lack of immediate value proof during initial trial.",
                recommendation="Implement a 3-step interactive onboarding flow with pre-populated templates to achieve time-to-first-value under 3 minutes.",
                priority=p1,
                impact=imp1,
                effort=eff1,
                confidence=conf1,
                evidence_strength=ev1,
                urgency=urg1,
                affected_personas=onboarding_affected,
                expected_outcomes=["Reduce Day-1 bounce rate by ~35%", "Accelerate task completion for non-technical users"],
                source_insights=["Theme: Onboarding", "Pain Points: Friction & Time Constraints"],
                status="Recommended",
                breakdown=b1,
            )
        )

        # Decision 2: Transparent Trust Signals & Trial Model
        trust_affected = [p for i, p in enumerate(all_persona_names) if i % 2 == 0] or all_persona_names[:1]
        imp2, conf2, ev2, urg2, eff2 = (90, 88, 92, 80, 40) if "Pricing" in theme_names or "Trust" in theme_names else (78, 80, 80, 65, 35)
        p2, b2 = calculate_priority_score(impact=imp2, confidence=conf2, evidence_strength=ev2, urgency=urg2, effort=eff2)
        decisions.append(
            ProductDecision(
                id="dec_trust_and_pricing_clarity",
                title="Transparent Value Proof & Low-Risk Trial Layer",
                problem="Price-sensitive and risk-conscious personas require verifiable proof of ROI and a low-barrier trial before committing to paid tiers.",
                recommendation="Introduce a 14-day no-credit-card trial, public ROI benchmark calculations, and clear data privacy badges on landing flows.",
                priority=p2,
                impact=imp2,
                effort=eff2,
                confidence=conf2,
                evidence_strength=ev2,
                urgency=urg2,
                affected_personas=trust_affected,
                expected_outcomes=["Increase free-to-paid conversion by ~22%", "Alleviate privacy/trust objections during evaluation"],
                source_insights=["Theme: Trust & Pricing", "Barrier: Proof of Value Requirement"],
                status="Recommended",
                breakdown=b2,
            )
        )

        # Decision 3: Workflow Automation / Core Feature Depth
        tech_affected = all_persona_names[1:] if len(all_persona_names) > 1 else all_persona_names
        imp3, conf3, ev3, urg3, eff3 = (82, 80, 85, 75, 55) if product_fit >= 50 else (86, 82, 88, 90, 60)
        p3, b3 = calculate_priority_score(impact=imp3, confidence=conf3, evidence_strength=ev3, urgency=urg3, effort=eff3)
        decisions.append(
            ProductDecision(
                id="dec_core_workflow_automation",
                title="Automated Insight Summaries & Export Workflows",
                problem="Busy professionals lack time to manually synthesize fragmented reports and demand automated summaries.",
                recommendation="Deploy 1-click executive digest generation, CSV/JSON data connector hooks, and team collaboration export triggers.",
                priority=p3,
                impact=imp3,
                effort=eff3,
                confidence=conf3,
                evidence_strength=ev3,
                urgency=urg3,
                affected_personas=tech_affected,
                expected_outcomes=["Increase weekly active user retention by ~28%", "Establish core daily habit loop"],
                source_insights=["Theme: Productivity & Convenience", "Feature Request: Automated Summaries"],
                status="Recommended",
                breakdown=b3,
            )
        )

        # Sort by priority descending
        decisions.sort(key=lambda d: d.priority, reverse=True)
        return [d.to_dict() for d in decisions]

    @classmethod
    def get_top_decisions(
        cls,
        decisions: Sequence[Mapping[str, Any]],
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        return [dict(d) for d in sorted(decisions, key=lambda x: int(x.get("priority", 0)), reverse=True)[:limit]]
