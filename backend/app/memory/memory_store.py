class MemoryStore:
    def __init__(self):
        self.memories = {}

    def save_memory(self, persona_id, message):
        if persona_id not in self.memories:
            self.memories[persona_id] = []

        self.memories[persona_id].append(message)

    def get_memory(self, persona_id):
        return self.memories.get(persona_id, [])

    def clear_memory(self, persona_id):
        if persona_id in self.memories:
            del self.memories[persona_id]