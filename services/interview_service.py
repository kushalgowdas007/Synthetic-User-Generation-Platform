from __future__ import annotations

from datetime import datetime, timezone
from collections import Counter
from typing import Any, Dict, List, Mapping

from backend.app.memory.memory_store import MemoryStore


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
    if any(word in lower_message for word in ["price", "cost", "pay", "buy", "subscription"]):
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
        if item.get("role") == "persona" and str(item.get("message", "")).strip()
    ]
    if not persona_messages:
        return "No interview responses have been captured yet."

    topic_counter = Counter(str(item.get("topic", "general_feedback")) for item in history if item.get("role") == "persona")
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


def _consistency_score(memory_payload: Mapping[str, Any]) -> int:
    opinions = dict(memory_payload.get("opinions", {}))
    history = [item for item in memory_payload.get("history", []) if isinstance(item, Mapping)]
    if not history:
        return 100

    score = 100
    topic_counts = Counter(str(item.get("topic", "")) for item in history if item.get("role") == "persona")
    repeated_topics = sum(1 for _, count in topic_counts.items() if count > 1)
    if repeated_topics and not opinions:
        score -= 15
    for topic in topic_counts:
        if topic and topic not in opinions:
            score -= 5
    return max(65, min(100, score))


def generate_interview_reply(
    persona: Mapping[str, Any],
    user_message: str,
    memory_payload: Mapping[str, Any],
    experiment: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Generate a deterministic persona-consistent interview reply and update memory."""
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
            f"My view is consistent with what I said earlier: {previous_opinion[:150]} "
            f"The short version is that {product} still has to match my real-world constraints."
        )
    elif opinion_topic == "pricing":
        answer_focus = f"I would need pricing to feel fair against the time saved. My buying style is: {buying}."
    elif opinion_topic == "pain_points":
        answer_focus = f"My biggest friction is {pain_points[0]}. If {product} reduces that, I would take it seriously."
    elif opinion_topic == "adoption":
        answer_focus = f"I would try it if onboarding is simple and it clearly supports my goal to {goals[0].lower()}."
    elif opinion_topic == "feature_requests":
        answer_focus = f"I would look for features that reduce {pain_points[0].lower()} and help me {goals[0].lower()}."
    elif opinion_topic == "recommendation":
        answer_focus = f"I would recommend it only if the first experience proves value quickly for people like me."
    else:
        answer_focus = f"As a {occupation}, I would judge {product} by whether it helps me {goals[0].lower()} without adding complexity."

    emotional_state = _emotion_for_topic(opinion_topic, persona)
    reply = (
        f"Speaking as {persona_name}, I am {tone} and currently {emotional_state}. {answer_focus} "
        f"My technology comfort is {tech}, so I prefer a workflow that feels clear, guided, and trustworthy."
    )

    memory.add_message("user", user_message, opinion_topic)
    memory.add_message("persona", reply, opinion_topic)
    memory.add_opinion(opinion_topic, reply)

    updated_history = history + [
        {"role": "user", "message": user_message, "topic": opinion_topic, "timestamp": datetime.now(timezone.utc).isoformat()},
        {
            "role": "persona",
            "message": reply,
            "topic": opinion_topic,
            "emotional_state": emotional_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]
    updated_payload = dict(memory_payload)
    updated_payload["history"] = updated_history
    updated_payload.setdefault("opinions", {})
    updated_payload["opinions"][opinion_topic] = reply
    updated_payload["emotional_state"] = emotional_state
    updated_payload["conversation_summary"] = _summarize_history(updated_history, persona_name)
    updated_payload["follow_up_questions"] = _build_follow_ups(opinion_topic, persona, product)
    updated_payload["last_updated"] = datetime.now(timezone.utc).isoformat()
    updated_payload["consistency_score"] = _consistency_score(updated_payload)

    return {
        "reply": reply,
        "memory": updated_payload,
        "quote": reply,
        "sentiment": "positive" if "try" in reply.lower() or "seriously" in reply.lower() else "neutral",
        "emotional_state": emotional_state,
        "follow_up_questions": updated_payload["follow_up_questions"],
        "conversation_summary": updated_payload["conversation_summary"],
        "consistency_score": updated_payload["consistency_score"],
    }


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
