from __future__ import annotations

import logging
import os
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from backend.app.memory.memory_store import MemoryStore
from services.persona_consistency import check_interview_consistency
from services.telemetry import telemetry

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - optional dependency guard
    genai = None
    types = None

logger = logging.getLogger("ai_research_studio.interview_service")


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


def create_memory_payload(persona: Mapping[str, Any]) -> Dict[str, Any]:
    initial_follow_ups = [
        "What would make this product feel trustworthy?",
        "Which feature would you try first?",
        "What would stop you from adopting it?",
    ]
    return {
        "persona_id": str(persona.get("id", persona.get("name", "persona"))),
        "persona_name": str(persona.get("name", "Persona")),
        "history": [],
        "opinions": {},
        "conversation_summary": "No interview responses have been captured yet.",
        "emotional_state": "neutral",
        "follow_up_questions": initial_follow_ups,
        "consistency_score": 100,
        "contradictions": [],
        "demographics": {
            "name": str(persona.get("name", "Persona")),
            "age": str(persona.get("age", "Unknown")),
            "occupation": str(persona.get("occupation", "Not provided")),
        },
    }


def _memory_from_payload(payload: Mapping[str, Any]) -> MemoryStore:
    memory = MemoryStore()
    for message in payload.get("history", []):
        if isinstance(message, Mapping):
            memory.add_message(str(message.get("role", "")), str(message.get("message", "")))
    for topic, opinion in dict(payload.get("opinions", {})).items():
        memory.add_opinion(str(topic), str(opinion))
    for key, value in dict(payload.get("demographics", {})).items():
        memory.set_demographic(str(key), str(value))
    return memory


def _response_tone(persona: Mapping[str, Any]) -> str:
    big_five = persona.get("big_five_personality") or persona.get("big_five") or {}
    openness = int(big_five.get("openness", 60)) if isinstance(big_five, Mapping) else 60
    neuroticism = int(big_five.get("neuroticism", 35)) if isinstance(big_five, Mapping) else 35
    if openness > 75 and neuroticism < 45:
        return "curious and optimistic"
    if neuroticism > 55:
        return "careful and risk-aware"
    return "practical and balanced"


def _topic_for_message(message: str) -> str:
    lower_message = message.lower()
    if any(word in lower_message for word in ["price", "cost", "pay", "buy", "subscription", "pricing"]):
        return "pricing"
    if any(word in lower_message for word in ["problem", "pain", "frustrat", "challenge", "barrier"]):
        return "pain_points"
    if any(word in lower_message for word in ["use", "adopt", "try", "switch", "onboarding"]):
        return "adoption"
    if any(word in lower_message for word in ["feature", "request", "missing", "improve"]):
        return "feature_requests"
    if any(word in lower_message for word in ["recommend", "share", "refer"]):
        return "recommendation"
    return "general_feedback"


def _emotion_for_topic(topic: str, persona: Mapping[str, Any]) -> str:
    big_five = persona.get("big_five_personality") or persona.get("big_five") or {}
    openness = int(big_five.get("openness", 60)) if isinstance(big_five, Mapping) else 60
    neuroticism = int(big_five.get("neuroticism", 35)) if isinstance(big_five, Mapping) else 35
    if topic in {"pricing", "pain_points"} and neuroticism >= 50:
        return "concerned"
    if topic in {"adoption", "feature_requests"} and openness >= 70:
        return "curious"
    if topic == "recommendation":
        return "confident"
    return "thoughtful"


def _summarize_history(history: List[Mapping[str, Any]], persona_name: str) -> str:
    persona_messages = [
        str(item.get("message", ""))
        for item in history
        if item.get("role") in ("persona", "assistant") and str(item.get("message", "")).strip()
    ]
    if not persona_messages:
        return "No interview responses have been captured yet."

    topic_counter = Counter(str(item.get("topic", "general_feedback")) for item in history if item.get("role") in ("persona", "assistant"))
    top_topic = topic_counter.most_common(1)[0][0].replace("_", " ") if topic_counter else "general feedback"
    latest = persona_messages[-1]
    return f"{persona_name} has focused on {top_topic}. Latest signal: {latest[:180]}"


def _build_follow_ups(topic: str, persona: Mapping[str, Any], product: str) -> List[str]:
    pain_points = _as_list(persona.get("pain_points")) or ["friction"]
    goals = _as_list(persona.get("goals")) or ["save time"]
    if topic == "pricing":
        return [
            f"What price point would make {product} feel low-risk?",
            "Would a free trial change your willingness to buy?",
            "What proof of ROI would you need first?",
        ]
    if topic == "pain_points":
        return [
            f"How often does {pain_points[0].lower()} affect your current workflow?",
            f"What would convince you that {product} solves that pain point?",
            "Which workaround do you use today?",
        ]
    if topic == "feature_requests":
        return [
            "Which missing feature would matter most on day one?",
            "Would personalization or automation be more valuable?",
            "What integration would make this easier to adopt?",
        ]
    return [
        f"What would make {product} clearly help you {goals[0].lower()}?",
        "What would you need to see in the first five minutes?",
        "Who else would influence your adoption decision?",
    ]


def generate_interview_reply(
    persona: Mapping[str, Any],
    user_message: str,
    memory_payload: Mapping[str, Any],
    experiment: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Generate a persona-consistent Gemini response with memory tracking, audit, and local fallback."""
    memory = _memory_from_payload(memory_payload)
    product = str((experiment or {}).get("product_name") or "this product")
    persona_name = str(persona.get("name", "Persona"))
    occupation = str(persona.get("occupation", "professional"))
    goals = _as_list(persona.get("goals")) or ["save time"]
    pain_points = _as_list(persona.get("pain_points")) or ["too much friction"]
    buying = str(persona.get("buying_behavior") or persona.get("buying_behaviour") or "compares value before buying")
    tech = str(persona.get("technology_usage") or "Medium")
    tone = _response_tone(persona)
    history = list(memory_payload.get("history", []))
    opinion_topic = _topic_for_message(user_message)
    previous_opinion = memory.get_opinion(opinion_topic)

    if previous_opinion:
        answer_focus = (
            f"My view aligns with what I mentioned before: {previous_opinion[:140]}... "
            f"Overall, {product} needs to fit my real workflow."
        )
    elif opinion_topic == "pricing":
        answer_focus = f"I need pricing to be clearly justified by time saved. My buying style: {buying}."
    elif opinion_topic == "pain_points":
        answer_focus = f"My primary blocker is {pain_points[0]}. If {product} solves that, I would evaluate it seriously."
    elif opinion_topic == "adoption":
        answer_focus = f"I would try it if onboarding is fast and it helps me {goals[0].lower()} without complexity."
    elif opinion_topic == "feature_requests":
        answer_focus = f"I am looking for features that reduce {pain_points[0].lower()} and help me {goals[0].lower()}."
    elif opinion_topic == "recommendation":
        answer_focus = f"I would recommend {product} only after seeing concrete proof of value for my daily work."
    else:
        answer_focus = f"As a {occupation}, I assess {product} on whether it helps me {goals[0].lower()} reliably."

    emotional_state = _emotion_for_topic(opinion_topic, persona)
    fallback_reply = (
        f"Speaking as {persona_name}, I am {tone}. {answer_focus} "
        f"With my {tech} tech familiarity, I prefer guided, trustworthy workflows."
    )

    gemini_reply = _generate_gemini_reply(
        persona=persona,
        question=user_message,
        product=product,
        history=history,
        opinions=memory_payload.get("opinions", {}),
    )

    reply = gemini_reply or fallback_reply
    source = "gemini" if gemini_reply else "local_fallback"

    memory.add_message("user", user_message, opinion_topic)
    memory.add_message("persona", reply, opinion_topic)
    memory.add_opinion(opinion_topic, reply)

    now_iso = datetime.now(timezone.utc).isoformat()
    updated_history = history + [
        {"role": "user", "message": user_message, "topic": opinion_topic, "timestamp": now_iso},
        {
            "role": "persona",
            "message": reply,
            "topic": opinion_topic,
            "emotional_state": emotional_state,
            "timestamp": now_iso,
        },
    ]

    updated_opinions = dict(memory_payload.get("opinions", {}))
    updated_opinions[opinion_topic] = reply

    # Audit conversation consistency
    audit_report = check_interview_consistency(persona, updated_history, updated_opinions)

    updated_payload = dict(memory_payload)
    updated_payload["history"] = updated_history
    updated_payload["opinions"] = updated_opinions
    updated_payload["emotional_state"] = emotional_state
    updated_payload["conversation_summary"] = _summarize_history(updated_history, persona_name)
    updated_payload["follow_up_questions"] = _build_follow_ups(opinion_topic, persona, product)
    updated_payload["last_updated"] = now_iso
    updated_payload["consistency_score"] = audit_report.get("consistency_score", 100)
    updated_payload["contradictions"] = audit_report.get("contradictions", [])
    updated_payload["warnings"] = audit_report.get("warnings", [])

    sentiment = "positive" if any(w in reply.lower() for w in ("try", "valuable", "useful", "seriously", "love")) else "neutral"

    return {
        "reply": reply,
        "memory": updated_payload,
        "quote": reply,
        "sentiment": sentiment,
        "emotional_state": emotional_state,
        "follow_up_questions": updated_payload["follow_up_questions"],
        "conversation_summary": updated_payload["conversation_summary"],
        "consistency_score": updated_payload["consistency_score"],
        "contradictions": updated_payload["contradictions"],
        "source": source,
    }


def _generate_gemini_reply(
    *, persona: Mapping[str, Any], question: str, product: str, history: List[Any], opinions: Any,
) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or genai is None or types is None:
        return None

    context = "\n".join(
        f"{item.get('role', 'unknown')}: {item.get('message', '')}" for item in history[-8:] if isinstance(item, Mapping)
    ) or "No previous conversation."
    prompt = f"""Respond as the following synthetic research participant in first person. Never break character or claim to be AI.
Keep all demographic, behavioral, and opinion details strictly consistent. Be concise (2-4 sentences), specific, and realistic.
Persona: {dict(persona)}
Product: {product}
Known opinions: {opinions}
Conversation history:
{context}
Interviewer question: {question}
"""
    client = genai.Client(api_key=api_key)
    for attempt in range(3):
        try:
            telemetry.record_api_call("gemini")
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.65, max_output_tokens=250),
            )
            text = str(getattr(response, "text", "")).strip()
            if text:
                return text
        except Exception as exc:
            telemetry.record_retry("interview_gemini", attempt + 1)
            time.sleep(0.5 * (2**attempt))
            logger.warning("Gemini interview attempt %d failed: %s", attempt + 1, exc)
    return None


def flatten_interview_memories(memories: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for persona_id, memory in memories.items():
        if not isinstance(memory, Mapping):
            continue
        for item in memory.get("history", []):
            if isinstance(item, Mapping):
                rows.append(
                    {
                        "persona_id": persona_id,
                        "persona_name": memory.get("persona_name", persona_id),
                        "role": item.get("role", ""),
                        "message": item.get("message", ""),
                        "topic": item.get("topic", ""),
                        "emotional_state": item.get("emotional_state", memory.get("emotional_state", "")),
                        "timestamp": item.get("timestamp", ""),
                    }
                )
    return rows
