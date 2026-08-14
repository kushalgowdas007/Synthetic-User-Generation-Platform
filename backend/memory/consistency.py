from typing import Dict, List


class ConsistencyChecker:
    """Check direct demographic and preference contradictions in interview replies."""

    def check_persona(self, persona: Dict, response: str) -> Dict[str, object]:
        response_lower = response.lower()
        contradictions: List[str] = []
        age = str(persona.get("age", "")).lower()
        if age and ("years old" in response_lower or "my age" in response_lower) and age not in response_lower:
            contradictions.append(f"Age should remain {age}")
        occupation = str(persona.get("occupation", "")).lower()
        if occupation and any(token in response_lower for token in ("my job", "i work", "occupation")) and occupation not in response_lower:
            contradictions.append("Occupation mismatch")
        location = str(persona.get("location", "")).lower()
        if location and "i live" in response_lower and location not in response_lower:
            contradictions.append("Location mismatch")
        return {"consistent": not contradictions, "contradictions": contradictions}

    def check_history(self, previous_messages: List[str], new_response: str) -> Dict[str, object]:
        previous = " ".join(previous_messages).lower()
        current = new_response.lower()
        pairs = {
            "Coffee preference changed": ("hate coffee", "love coffee"),
            "Technology preference changed": ("android", "iphone only"),
            "Shopping preference changed": ("online shopping", "never shop online"),
        }
        contradictions = [label for label, (old, new) in pairs.items() if old in previous and new in current]
        return {"consistent": not contradictions, "contradictions": contradictions}

    def check(self, old_data: List[str], new_response: str) -> Dict[str, object]:
        """Compatibility helper retained for the original command-line smoke test."""
        return self.check_history(old_data, new_response)
