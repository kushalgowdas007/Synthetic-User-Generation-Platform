from backend.app.memory.memory_store import MemoryStore
from backend.app.memory.consistency_checker import ConsistencyChecker

memory = MemoryStore()

memory.save_memory("user1", "I like coffee")
memory.save_memory("user1", "I use Android")

print(memory.get_memory("user1"))

checker = ConsistencyChecker()

persona = {
    "name": "John",
    "age": 25,
    "gender": "Male",
    "occupation": "Engineer"
}

print(checker.demographic_validation(persona))
print(checker.behavior_validation(memory.get_memory("user1")))
print(checker.consistency_score(10, 9))