from typing import Dict, List

class MemoryStore:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.opinions: Dict[str, str] = {}
        self.demographics: Dict[str, str] = {}

    def add_message(self, role: str, message: str):
        self.conversation_history.append({
            "role": role,
            "message": message
        })

    def get_history(self):
        return self.conversation_history

    def add_opinion(self, topic: str, opinion: str):
        self.opinions[topic] = opinion

    def get_opinion(self, topic: str):
        return self.opinions.get(topic)

    def set_demographic(self, key: str, value: str):
        self.demographics[key] = value

    def get_demographic(self, key: str):
        return self.demographics.get(key)

    def clear_memory(self):
        self.conversation_history.clear()
        self.opinions.clear()
        self.demographics.clear()