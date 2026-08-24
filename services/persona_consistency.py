from __future__ import annotations

import re
<<<<<<< HEAD
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence


@dataclass
class ContradictionFlag:
    turn_index: Optional[int]
    turn_reference: str
    category: str
    description: str
    severity: str  # "high", "medium", "info"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterviewConsistencyReport:
    consistency_score: int
    contradictions: List[ContradictionFlag] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    supporting_turns: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consistency_score": self.consistency_score,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "warnings": self.warnings,
            "supporting_turns": self.supporting_turns,
        }


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


class PersonaConsistencyEngine:
    """Evaluates behavioral, preference, and cross-channel consistency across research touchpoints."""

    CONTRADICTION_PAIRS = [
        ("price_sensitivity", ["price sensitive", "budget tight", "cost-conscious", "low budget"], ["pay any amount", "money is no object", "unlimited budget", "immediately pay 10000"]),
        ("privacy", ["don't share data", "no health data", "strict privacy", "refuse data"], ["comfortable sharing all data", "share any data", "no privacy concerns"]),
        ("tech_adoption", ["hate new tech", "low tech", "refuse automation", "too complex"], ["automation-first", "early adopter of everything", "build custom api"]),
        ("decision_style", ["need detailed proof", "cautious buyer", "compare everything"], ["impulse buyer", "buy without checking", "never read reviews"]),
    ]

    @classmethod
    def audit_interview_history(
        cls,
        persona: Mapping[str, Any],
        history: Sequence[Mapping[str, Any]],
        opinions: Mapping[str, Any],
    ) -> InterviewConsistencyReport:
        """
        Audits a persona's complete interview transcript for contradictions and opinion drift.
        Returns a normalized consistency score (0-100) with detailed turn citations.
        """
        contradictions: List[ContradictionFlag] = []
        warnings: List[str] = []
        supporting_turns: List[Dict[str, Any]] = []
        
        persona_turns = [
            (idx, turn)
            for idx, turn in enumerate(history, 1)
            if turn.get("role") in ("persona", "assistant")
        ]

        if not persona_turns:
            return InterviewConsistencyReport(consistency_score=100, warnings=["No persona responses to audit yet."])

        all_text = " ".join(str(turn.get("message", "")) for _, turn in persona_turns).lower()
        score = 100

        # 1. Check direct persona profile contradictions in interview
        age_str = str(persona.get("age", "")).lower()
        occupation = str(persona.get("occupation", "")).lower()

        for turn_num, turn in persona_turns:
            msg = str(turn.get("message", "")).lower()
            topic = str(turn.get("topic", "general"))
            
            # Record supporting turns
            supporting_turns.append({
                "turn": turn_num,
                "topic": topic,
                "snippet": msg[:100],
                "emotion": str(turn.get("emotional_state", "neutral")),
            })

            # Check if persona claimed a different occupation
            if "i am a" in msg or "my job as a" in msg:
                if occupation and not any(part in msg for part in occupation.split()):
                    contradictions.append(
                        ContradictionFlag(
                            turn_index=turn_num,
                            turn_reference=f"Turn {turn_num}",
                            category="Demographic Mismatch",
                            description=f"Statement may diverge from designated occupation '{persona.get('occupation')}'.",
                            severity="medium",
                        )
                    )
                    score -= 10

        # 2. Check semantic contradiction pairs across interview history
        for category, stance_a, stance_b in cls.CONTRADICTION_PAIRS:
            found_a = [turn_num for turn_num, turn in persona_turns if any(p in str(turn.get("message", "")).lower() for p in stance_a)]
            found_b = [turn_num for turn_num, turn in persona_turns if any(p in str(turn.get("message", "")).lower() for p in stance_b)]

            if found_a and found_b:
                contradictions.append(
                    ContradictionFlag(
                        turn_index=found_b[0],
                        turn_reference=f"Turn {found_a[0]} vs Turn {found_b[0]}",
                        category=category.replace("_", " ").title(),
                        description=f"Conflicting stances detected on {category.replace('_', ' ')} between Turn {found_a[0]} and Turn {found_b[0]}.",
                        severity="high",
                    )
                )
                score -= 20

        # 3. Check stability across recorded opinions
        for topic, op_text in opinions.items():
            if not op_text:
                continue
            related_turns = [turn for _, turn in persona_turns if str(turn.get("topic", "")) == topic]
            if len(related_turns) >= 2:
                first_msg = str(related_turns[0].get("message", "")).lower()
                last_msg = str(related_turns[-1].get("message", "")).lower()
                # If first was negative and last is enthusiastic without transition
                if ("not likely" in first_msg or "too expensive" in first_msg) and ("extremely likely" in last_msg or "cheap" in last_msg):
                    warnings.append(f"Noticeable sentiment shift on topic '{topic}' across conversation turns.")
                    score -= 8

        consistency_score = max(50, min(100, score))
        return InterviewConsistencyReport(
            consistency_score=consistency_score,
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
        Verifies alignment between quantitative survey scores, 1-on-1 interview messages,
        and focus-group statements for a single persona.
        """
        persona_name = str(persona.get("name", "Persona"))
        
        # Survey signal
        persona_surveys = [r for r in survey_responses if str(r.get("persona_name", "")).strip().lower() == persona_name.lower()]
        survey_scores = [float(r.get("score", 50) or 50) for r in persona_surveys]
        avg_survey_score = sum(survey_scores) / len(survey_scores) if survey_scores else None

        # Interview & Focus Group text
        persona_interviews = [r for r in interview_history if str(r.get("persona_name", "")).strip().lower() == persona_name.lower() or str(r.get("role")) == "persona"]
        interview_text = " ".join(str(r.get("message", "")) for r in persona_interviews).lower()

        persona_focus = [r for r in focus_group_turns if str(r.get("speaker", "")).strip().lower() == persona_name.lower()]
        focus_text = " ".join(str(r.get("message", "")) for r in persona_focus).lower()

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


def check_interview_consistency(
    persona: Mapping[str, Any],
    conversation_history: Sequence[Mapping[str, Any]],
    opinions: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Top-level convenience function returning the interview consistency audit report."""
    report = PersonaConsistencyEngine.audit_interview_history(
        persona=persona,
        history=conversation_history,
        opinions=opinions or {},
    )
    return report.to_dict()
=======
from typing import Any, Dict, List, Mapping, Sequence
from models.schemas import ContradictionItem, InterviewConsistencyReport


def check_interview_consistency(history: Sequence[Mapping[str, Any]], persona_profile: Mapping[str, Any]) -> InterviewConsistencyReport:
    """
    Audit synthetic interview memory and conversation history for persona-profile consistency
    and self-contradictions across conversation turns.
    """
    if not history:
        return InterviewConsistencyReport(consistency_score=100, contradictions=[], warnings=[], supporting_turns=[])

    contradictions: List[ContradictionItem] = []
    warnings: List[str] = []
    supporting_turns: List[Dict[str, str]] = []
    
    score = 100

    # Extract user-assistant turn pairs
    turns: List[Tuple[str, str]] = []
    current_user = ""
    for item in history:
        role = item.get("role")
        msg = str(item.get("message", "")).strip()
        if role == "user":
            current_user = msg
        elif role == "assistant" and current_user:
            turns.append((current_user, msg))
            current_user = ""

    # Rule-based contradiction checks across turns
    # 1. Price sensitivity vs willingness to pay huge sum
    price_sensitive = False
    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if any(phrase in text for phrase in ["tight budget", "price sensitive", "too expensive", "hard to justify cost", "cannot afford"]):
            price_sensitive = True

    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if price_sensitive and any(phrase in text for phrase in ["immediately pay 10,000", "price is not an issue", "cost does not matter", "happily pay premium"]):
            score -= 20
            item = ContradictionItem(
                turn_user=user_msg,
                turn_assistant=assistant_msg,
                topic="Pricing & Budget",
                contradiction="Stated price sensitivity in earlier turns but expressed unconstrained payment willingness in later turn.",
                severity="High"
            )
            contradictions.append(item)
            warnings.append("⚠ Potential inconsistency: Price sensitivity vs. unconstrained payment willingness.")

    # 2. Data privacy / health sharing contradictions
    privacy_strict = False
    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if any(phrase in text for phrase in ["don't share health data", "never share personal data", "privacy is non-negotiable", "strict data privacy"]):
            privacy_strict = True

    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if privacy_strict and any(phrase in text for phrase in ["comfortable sharing all health data", "don't mind sharing my data", "openly share data"]):
            score -= 20
            item = ContradictionItem(
                turn_user=user_msg,
                turn_assistant=assistant_msg,
                topic="Privacy & Trust",
                contradiction="Stated strict privacy boundaries in earlier turn but agreed to share sensitive personal data later.",
                severity="High"
            )
            contradictions.append(item)
            warnings.append("⚠ Potential inconsistency: Data privacy boundary shift.")

    # 3. Technology stance contradiction
    tech_reluctant = False
    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if any(phrase in text for phrase in ["prefer manual process", "don't trust ai", "not comfortable with tech", "prefer paper"]):
            tech_reluctant = True

    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if tech_reluctant and any(phrase in text for phrase in ["love automated ai", "ai is my main workflow", "fully automated solution"]):
            score -= 15
            item = ContradictionItem(
                turn_user=user_msg,
                turn_assistant=assistant_msg,
                topic="Technology Adoption",
                contradiction="Expressed AI reluctance earlier but embraced full automation in subsequent response.",
                severity="Medium"
            )
            contradictions.append(item)
            warnings.append("⚠ Potential inconsistency: AI reluctance vs. automation enthusiasm.")

    # Profile vs Interview checks
    persona_tech = str(persona_profile.get("technology_usage", "")).lower()
    for user_msg, assistant_msg in turns:
        text = assistant_msg.lower()
        if "low" in persona_tech and any(phrase in text for phrase in ["built custom webhooks", "advanced API integration", "write script"]):
            score -= 10
            warnings.append("⚠ Turn claims advanced developer action despite Low tech usage profile.")

    # Format supporting turns for audit preview
    for idx, (u, a) in enumerate(turns, 1):
        supporting_turns.append({
            "turn": f"Turn {idx}",
            "question": u[:60] + ("..." if len(u) > 60 else ""),
            "answer": a[:100] + ("..." if len(a) > 100 else "")
        })

    return InterviewConsistencyReport(
        consistency_score=max(0, min(100, score)),
        contradictions=contradictions,
        warnings=warnings,
        supporting_turns=supporting_turns,
    )
>>>>>>> f68520b (Save local changes)
