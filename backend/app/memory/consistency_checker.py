from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence


class ConsistencyChecker:
    @staticmethod
    def check_opinion(old_opinion: Any, new_opinion: Any) -> bool:
        old_text = str(old_opinion or "").strip().lower()
        new_text = str(new_opinion or "").strip().lower()
        if not old_text or not new_text:
            return True
        return old_text == new_text or old_text in new_text or new_text in old_text

    @staticmethod
    def validate_demographics(demographics: Mapping[str, Any]) -> bool:
        required_fields = ["name", "age"]
        return all(str(demographics.get(field, "")).strip() for field in required_fields)

    @staticmethod
    def validate_behavior(history: Sequence[Mapping[str, Any]]) -> bool:
        if history is None:
            return False
        topics = Counter(str(item.get("topic", "")) for item in history if isinstance(item, Mapping))
        return all(count >= 0 for count in topics.values())

    @staticmethod
    def logical_consistency(history: Sequence[Mapping[str, Any]] | None = None) -> bool:
        if not history:
            return True
        for item in history:
            message = str(item.get("message", "")).lower() if isinstance(item, Mapping) else ""
            if "definitely would buy" in message and "never buy" in message:
                return False
        return True

    @staticmethod
    def consistency_score(matches: int, total: int) -> float:
        if total == 0:
            return 100.0
        return round((matches / total) * 100, 2)

    @classmethod
    def validate_memory_payload(cls, payload: Mapping[str, Any]) -> dict:
        demographics_valid = cls.validate_demographics(payload.get("demographics", {}))
        behavior_valid = cls.validate_behavior(payload.get("history", []))
        logical_valid = cls.logical_consistency(payload.get("history", []))
        matches = sum([demographics_valid, behavior_valid, logical_valid])
        return {
            "demographics_valid": demographics_valid,
            "behavior_valid": behavior_valid,
            "logical_valid": logical_valid,
            "consistency_score": cls.consistency_score(matches, 3),
        }
