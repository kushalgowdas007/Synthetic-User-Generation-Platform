from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Mapping

from backend.app.memory.memory_store import MemoryStore

try:  # Gemini is optional; deterministic responses keep demos functional offline.
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - dependency/environment guard
    genai = None
    types = None


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
    return {
        "persona_id": str(persona.get("id", persona.get("name", "persona"))),
        "persona_name": str(persona.get("name", "Persona")),
        "history": [],
        "opinions": {},
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


def generate_interview_reply(
    persona: Mapping[str, Any],
    user_message: str,
    memory_payload: Mapping[str, Any],
    experiment: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Generate a persona-consistent Gemini response, with a reliable local fallback."""
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

    lower_message = user_message.lower()
    if any(word in lower_message for word in ["price", "cost", "pay", "buy"]):
        opinion_topic = "pricing"
        answer_focus = f"I would need pricing to feel fair against the time saved. My buying style is: {buying}."
    elif any(word in lower_message for word in ["problem", "pain", "frustrat", "challenge"]):
        opinion_topic = "pain_points"
        answer_focus = f"My biggest friction is {pain_points[0]}. If {product} reduces that, I would take it seriously."
    elif any(word in lower_message for word in ["use", "adopt", "try", "switch"]):
        opinion_topic = "adoption"
        answer_focus = f"I would try it if onboarding is simple and it clearly supports my goal to {goals[0].lower()}."
    else:
        opinion_topic = "general_feedback"
        answer_focus = f"As a {occupation}, I would judge {product} by whether it helps me {goals[0].lower()} without adding complexity."

    fallback_reply = (
        f"Speaking as {persona_name}, I am {tone}. {answer_focus} "
        f"My technology comfort is {tech}, so I prefer a workflow that feels clear, guided, and trustworthy."
    )

    reply = _generate_gemini_reply(
        persona=persona,
        question=user_message,
        product=product,
        history=history,
        opinions=memory_payload.get("opinions", {}),
    ) or fallback_reply

    memory.add_message("user", user_message)
    memory.add_message("persona", reply)
    memory.add_opinion(opinion_topic, reply)

    updated_history = history + [
        {"role": "user", "message": user_message, "timestamp": datetime.now(timezone.utc).isoformat()},
        {"role": "persona", "message": reply, "timestamp": datetime.now(timezone.utc).isoformat()},
    ]
    updated_payload = dict(memory_payload)
    updated_payload["history"] = updated_history
    updated_payload.setdefault("opinions", {})
    updated_payload["opinions"][opinion_topic] = reply

    return {
        "reply": reply,
        "memory": updated_payload,
        "quote": reply,
        "sentiment": "positive" if any(word in reply.lower() for word in ("try", "valuable", "useful", "seriously")) else "neutral",
        "source": "gemini" if reply != fallback_reply else "local_fallback",
    }


def _generate_gemini_reply(
    *, persona: Mapping[str, Any], question: str, product: str, history: List[Any], opinions: Any,
) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or genai is None or types is None:
        return None
    context = "\n".join(
        f"{item.get('role', 'unknown')}: {item.get('message', '')}" for item in history[-8:] if isinstance(item, Mapping)
    ) or "No previous conversation."
    prompt = f"""Respond as the following synthetic research participant, in first person. Never claim to be AI.
Keep all demographic, behavioral and opinion details consistent. Be concise (2-4 sentences), specific, and realistic.
Persona: {dict(persona)}
Product: {product}
Known opinions: {opinions}
Conversation: {context}
Interviewer question: {question}
"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), contents=prompt,
            config=types.GenerateContentConfig(temperature=0.65, max_output_tokens=240),
        )
        text = str(getattr(response, "text", "")).strip()
        return text if text else None
    except Exception:
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
                        "timestamp": item.get("timestamp", ""),
                    }
                )
    return rows
