from typing import Dict, List


class ConsistencyChecker:
    """
    Checks whether a persona contradicts previous
    memories or profile information.
    """

def check_persona(self, persona: Dict, response: str):

    response = response.lower()

    contradictions = []

    # Check age only if the response explicitly mentions age
    if "age" in response or "years old" in response:

        if "age" in persona:

            expected_age = str(persona["age"])

            if expected_age not in response:

                contradictions.append(
                    f"Age should remain {expected_age}"
                )

    # Check occupation only if occupation is mentioned
    if (
        "work" in response
        or "job" in response
        or "profession" in response
    ):

        occupation = persona.get(
            "occupation",
            ""
        ).lower()

        if occupation and occupation not in response:

            contradictions.append(
                "Occupation mismatch"
            )

    # Check location only if location is mentioned
    if "live" in response:

        location = persona.get(
            "location",
            ""
        ).lower()

        if location and location not in response:

            contradictions.append(
                "Location mismatch"
            )

    return {
        "consistent": len(contradictions) == 0,
        "contradictions": contradictions
    }
    def check_history(
        self,
        previous_messages: List[str],
        new_response: str
    ):

        contradictions = []

        previous = " ".join(previous_messages).lower()

        current = new_response.lower()

        if "hate coffee" in previous and "love coffee" in current:
            contradictions.append(
                "Coffee preference changed"
            )

        if "android" in previous and "iphone only" in current:
            contradictions.append(
                "Technology preference changed"
            )

        if "online shopping" in previous and "never shop online" in current:
            contradictions.append(
                "Shopping preference changed"
            )

        return {
            "consistent": len(contradictions) == 0,
            "contradictions": contradictions
        }