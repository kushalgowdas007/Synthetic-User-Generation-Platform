from typing import Dict, List
from datetime import datetime, timezone

from .models import ConversationMessage


class ConversationHistory:
    """
    Stores interview conversations for personas.
    """

    def __init__(self):
        self._history: Dict[str, List[ConversationMessage]] = {}


    def save_message(
        self,
        persona_id: str,
        role: str,
        message: str
    ):
        """
        Save one conversation message.
        
        role:
        - user
        - persona
        """

        conversation = ConversationMessage(
            role=role,
            message=message,
            timestamp=datetime.now(timezone.utc)
        )

        if persona_id not in self._history:
            self._history[persona_id] = []

        self._history[persona_id].append(conversation)

        return conversation



    def get_history(
        self,
        persona_id: str
    ) -> List[ConversationMessage]:
        """
        Get complete conversation history.
        """

        return self._history.get(persona_id, [])



    def get_last_message(
        self,
        persona_id: str
    ):
        """
        Get the latest message.
        """

        history = self._history.get(persona_id, [])

        if history:
            return history[-1]

        return None



    def clear_history(
        self,
        persona_id: str
    ):
        """
        Delete conversation history.
        """

        self._history[persona_id] = []
