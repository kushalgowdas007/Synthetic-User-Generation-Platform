from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


@dataclass
class ContradictionFlag:
    turn_index: Optional[int]
    turn_reference: str
    category: str
    description: str
    severity: str
    turn_user: str = ""
    turn_assistant: str = ""
    topic: str = ""
    contradiction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["topic"] = self.topic or self.category
        data["contradiction"] = self.contradiction or self.description
        return data


@dataclass
class InterviewConsistencyReport:
    consistency_score: int
    contradictions: List[ContradictionFlag] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    supporting_turns: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consistency_score": self.consistency_score,
            "contradictions": [contradiction.to_dict() for contradiction in self.contradictions],
            "warnings": self.warnings,
            "supporting_turns": self.supporting_turns,
        }


class PersonaConsistencyEngine:
    """Evaluates behavioral, preference, and cross-channel consistency across research touchpoints."""

    CONTRADICTION_PAIRS = [
        (
            "price_sensitivity",
            ["price sensitive", "budget tight", "cost-conscious", "low budget", "too expensive", "cannot afford"],
            ["pay any amount", "money is no object", "unlimited budget", "immediately pay 10000", "cost does not matter"],
        ),
        (
            "privacy",
            ["don't share data", "no health data", "strict privacy", "refuse data", "privacy is non-negotiable"],
            ["comfortable sharing all data", "share any data", "no privacy concerns", "openly share data"],
        ),
        (
            "tech_adoption",
            ["hate new tech", "low tech", "refuse automation", "too complex", "prefer manual process", "don't trust ai"],
            ["automation-first", "early adopter of everything", "build custom api", "fully automated solution"],
        ),
        (
            "decision_style",
            ["need detailed proof", "cautious buyer", "compare everything"],
            ["impulse buyer", "buy without checking", "never read reviews"],
        ),
    ]

    @classmethod
    def audit_interview_history(
        cls,
        persona: Mapping[str, Any],
        history: Sequence[Mapping[str, Any]],
        opinions: Mapping[str, Any],
    ) -> InterviewConsistencyReport:
        """
        Audit a persona transcript for profile mismatches, self-contradictions, and opinion drift.
        """
        contradictions: List[ContradictionFlag] = []
        warnings: List[str] = []
        supporting_turns: List[Dict[str, Any]] = []

        persona_turns = [
            (index, turn)
            for index, turn in enumerate(history, 1)
            if turn.get("role") in ("persona", "assistant")
        ]
        if not persona_turns:
            return InterviewConsistencyReport(
                consistency_score=100,
                warnings=["No persona responses to audit yet."],
            )

        score = 100
        occupation = str(persona.get("occupation", "")).lower()
        persona_tech = str(persona.get("technology_usage", "")).lower()

        for turn_number, turn in persona_turns:
            message = str(turn.get("message", "")).lower()
            topic = str(turn.get("topic", "general"))
            supporting_turns.append(
                {
                    "turn": f"Turn {turn_number}",
                    "topic": topic,
                    "snippet": message[:100],
                    "emotion": str(turn.get("emotional_state", "neutral")),
                }
            )

            if ("i am a" in message or "my job as a" in message) and occupation:
                if not any(part in message for part in occupation.split()):
                    contradictions.append(
                        ContradictionFlag(
                            turn_index=turn_number,
                            turn_reference=f"Turn {turn_number}",
                            category="Demographic Mismatch",
                            description=f"Statement may diverge from designated occupation '{persona.get('occupation')}'.",
                            severity="medium",
                        )
                    )
                    score -= 10

            if "low" in persona_tech and any(
                phrase in message
                for phrase in ("built custom webhooks", "advanced api integration", "write script")
            ):
                warnings.append("Turn claims advanced developer action despite low technology usage profile.")
                score -= 10

        for category, stance_a, stance_b in cls.CONTRADICTION_PAIRS:
            found_a = [
                turn_number
                for turn_number, turn in persona_turns
                if any(phrase in str(turn.get("message", "")).lower() for phrase in stance_a)
            ]
            found_b = [
                turn_number
                for turn_number, turn in persona_turns
                if any(phrase in str(turn.get("message", "")).lower() for phrase in stance_b)
            ]
            if found_a and found_b:
                readable = category.replace("_", " ").title()
                description = f"Conflicting stances detected on {category.replace('_', ' ')} between Turn {found_a[0]} and Turn {found_b[0]}."
                contradictions.append(
                    ContradictionFlag(
                        turn_index=found_b[0],
                        turn_reference=f"Turn {found_a[0]} vs Turn {found_b[0]}",
                        category=readable,
                        description=description,
                        severity="high",
                        topic=readable,
                        contradiction=description,
                    )
                )
                warnings.append(f"Potential inconsistency: {readable}.")
                score -= 20

        for topic, opinion_text in opinions.items():
            if not opinion_text:
                continue
            related_turns = [turn for _, turn in persona_turns if str(turn.get("topic", "")) == str(topic)]
            if len(related_turns) >= 2:
                first_message = str(related_turns[0].get("message", "")).lower()
                last_message = str(related_turns[-1].get("message", "")).lower()
                if ("not likely" in first_message or "too expensive" in first_message) and (
                    "extremely likely" in last_message or "cheap" in last_message
                ):
                    warnings.append(f"Noticeable sentiment shift on topic '{topic}' across conversation turns.")
                    score -= 8

        for user_message, assistant_message in _turn_pairs(history):
            text = assistant_message.lower()
            if any(phrase in text for phrase in ("happily pay premium", "price is not an issue")):
                prior_price_sensitivity = any(
                    any(phrase in earlier.lower() for phrase in ("tight budget", "price sensitive", "too expensive"))
                    for _, earlier in _turn_pairs(history)
                )
                if prior_price_sensitivity:
                    contradictions.append(
                        ContradictionFlag(
                            turn_index=None,
                            turn_reference="Conversation",
                            category="Pricing & Budget",
                            description="Persona expressed price sensitivity and later unconstrained payment willingness.",
                            severity="high",
                            turn_user=user_message,
                            turn_assistant=assistant_message,
                            topic="Pricing & Budget",
                            contradiction="Stated price sensitivity earlier but expressed unconstrained payment willingness later.",
                        )
                    )
                    score -= 15
                    break

        return InterviewConsistencyReport(
            consistency_score=max(0, min(100, score)),
            contradictions=contradictions,
            warnings=warnings,
            supporting_turns=supporting_turns,
        )

    @classmethod
    def audit_cross_channel_consistency(
        cls,
        persona: Mapping[str, Any],
        survey_responses: Sequence[Mapping[str, Any]],
        interview_history: Sequence[Mapping[str, Any]],
        focus_group_turns: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify alignment between quantitative survey scores and qualitative persona statements.
        """
        persona_name = str(persona.get("name", "Persona"))
        persona_surveys = [
            response
            for response in survey_responses
            if str(response.get("persona_name", "")).strip().lower() == persona_name.lower()
        ]
        survey_scores = [float(response.get("score", 50) or 50) for response in persona_surveys]
        avg_survey_score = sum(survey_scores) / len(survey_scores) if survey_scores else None

        persona_interviews = [
            row
            for row in interview_history
            if str(row.get("persona_name", "")).strip().lower() == persona_name.lower()
            or str(row.get("role")) == "persona"
        ]
        interview_text = " ".join(str(row.get("message", "")) for row in persona_interviews).lower()

        persona_focus = [
            row
            for row in focus_group_turns
            if str(row.get("speaker", "")).strip().lower() == persona_name.lower()
        ]
        focus_text = " ".join(str(row.get("message", "")) for row in persona_focus).lower()

        flags: List[str] = []
        alignment_score = 92
        if avg_survey_score is not None:
            if avg_survey_score < 40 and ("love this" in interview_text or "definitely adopt" in focus_text):
                flags.append(f"Low survey score ({avg_survey_score:.0f}/100) conflicts with highly positive verbal remarks.")
                alignment_score -= 15
            elif avg_survey_score > 75 and ("refuse to use" in interview_text or "too broken" in focus_text):
                flags.append(f"High survey score ({avg_survey_score:.0f}/100) conflicts with severe verbal objections.")
                alignment_score -= 15

        return {
            "persona_name": persona_name,
            "alignment_score": max(50, min(100, alignment_score)),
            "flags": flags,
            "status": "Consistent" if not flags else "Contextual Variance Detected",
        }


def _turn_pairs(history: Sequence[Mapping[str, Any]]) -> List[Tuple[str, str]]:
    turns: List[Tuple[str, str]] = []
    current_user = ""
    for item in history:
        role = item.get("role")
        message = str(item.get("message", "")).strip()
        if role == "user":
            current_user = message
        elif role in ("assistant", "persona") and current_user:
            turns.append((current_user, message))
            current_user = ""
    return turns


def check_interview_consistency(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Top-level convenience helper returning a dictionary consistency audit."""
    opinions = kwargs.get("opinions") or {}
    if len(args) >= 2 and isinstance(args[0], Mapping):
        persona = args[0]
        history = args[1]
        if len(args) >= 3:
            opinions = args[2] or {}
    elif len(args) >= 2:
        history = args[0]
        persona = args[1]
        if len(args) >= 3:
            opinions = args[2] or {}
    else:
        persona = kwargs.get("persona") or kwargs.get("persona_profile") or {}
        history = kwargs.get("history") or kwargs.get("conversation_history") or []

    report = PersonaConsistencyEngine.audit_interview_history(
        persona=persona,
        history=history,
        opinions=opinions,
    )
    return report.to_dict()
