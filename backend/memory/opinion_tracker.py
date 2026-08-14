from typing import Dict, List

from .models import Opinion


class OpinionTracker:
    """
    Stores persona opinions and preferences.
    """

    def __init__(self):
        self._opinions: Dict[str, List[Opinion]] = {}


    def add_opinion(
        self,
        persona_id: str,
        topic: str,
        value: str
    ):
        """
        Add a new opinion.
        """

        opinion = Opinion(
            topic=topic,
            value=value
        )

        if persona_id not in self._opinions:
            self._opinions[persona_id] = []

        self._opinions[persona_id].append(opinion)

        return opinion



    def get_opinions(
        self,
        persona_id: str
    ) -> List[Opinion]:
        """
        Get all opinions of a persona.
        """

        return self._opinions.get(persona_id, [])



    def get_opinion(
        self,
        persona_id: str,
        topic: str
    ):
        """
        Find opinion by topic.
        """

        opinions = self._opinions.get(persona_id, [])

        for opinion in opinions:
            if opinion.topic.lower() == topic.lower():
                return opinion

        return None



    def update_opinion(
        self,
        persona_id: str,
        topic: str,
        new_value: str
    ):
        """
        Update existing opinion.
        """

        opinion = self.get_opinion(
            persona_id,
            topic
        )

        if opinion:
            opinion.value = new_value
            return True

        return False



    def delete_opinion(
        self,
        persona_id: str,
        topic: str
    ):
        """
        Delete an opinion.
        """

        opinions = self._opinions.get(persona_id, [])

        for opinion in opinions:
            if opinion.topic.lower() == topic.lower():
                opinions.remove(opinion)
                return True

        return False