from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence


def _items(value: Any) -> list[str]:
    return value if isinstance(value, list) else [str(value)] if value else []


def run_focus_group(question: str, personas: Sequence[Mapping[str, Any]], experiment: Mapping[str, Any]) -> list[Dict[str, str]]:
    product = str(experiment.get("product_name") or "this product")
    turns: list[Dict[str, str]] = [{"speaker": "Moderator", "role": "moderator", "message": question}]
    positions = ["agrees", "challenges", "builds on", "disagrees with"]
    for index, persona in enumerate(list(personas)[:6]):
        name = str(persona.get("name") or "Participant")
        goal = (_items(persona.get("goals")) or ["save time"])[0]
        pain = (_items(persona.get("pain_points")) or ["unnecessary friction"])[0]
        behavior = str(persona.get("buying_behavior") or "needs clear value")
        position = positions[index % len(positions)]
        message = f"I {position} the group so far. For me, {product} is compelling if it helps me {str(goal).lower()}. I would still question {str(pain).lower()}, and {behavior.lower()} before I commit."
        turns.append({"speaker": name, "role": "participant", "message": message})
    return turns
