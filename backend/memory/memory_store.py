import uuid
from typing import Dict, List

from .models import MemoryItem


class MemoryStore:
    """
    Stores memories for every persona.
    Currently uses in-memory storage.
    """

    def __init__(self):
        self._store: Dict[str, List[MemoryItem]] = {}
        self.history = []
        self.opinions = {}

    def add_memory(self, persona_id: str, text: str) -> MemoryItem:
        """
        Add a new memory.
        """

        memory = MemoryItem(
            memory_id=str(uuid.uuid4()),
            persona_id=persona_id,
            text=text,
        )

        self._store.setdefault(persona_id, []).append(memory)

        return memory


    def add_message(self, role: str, message: str):
        """
        Store conversation messages.
        """

        self.history.append(
            {
                "role": role,
                "message": message
            }
        )


    def get_history(self):
        """
        Return stored conversation history.
        """

        return self.history


    def add_opinion(self, topic: str, opinion: str):
        """
        Store persona opinions.
        """

        self.opinions[topic] = opinion


    def get_opinion(self, topic: str):
        """
        Get stored opinion.
        """

        return self.opinions.get(topic)

    def get_memories(self, persona_id: str) -> List[MemoryItem]:
        """
        Return all memories for a persona.
        """

        return self._store.get(persona_id, [])

    def update_memory(self, persona_id: str, memory_id: str, new_text: str) -> bool:
        """
        Update an existing memory.
        """

        memories = self._store.get(persona_id, [])

        for memory in memories:
            if memory.memory_id == memory_id:
                memory.text = new_text
                return True

        return False

    def delete_memory(self, persona_id: str, memory_id: str) -> bool:
        """
        Delete a memory.
        """

        memories = self._store.get(persona_id, [])

        for memory in memories:
            if memory.memory_id == memory_id:
                memories.remove(memory)
                return True

        return False

    def clear_memories(self, persona_id: str):
        """
        Remove every memory of a persona.
        """

        self._store[persona_id] = []