from backend.app.memory.memory_store import MemoryStore
from backend.app.memory.consistency_checker import ConsistencyChecker


def test_memory_creation():
    memory = MemoryStore()

    memory.add_message("user", "Hello")
    assert len(memory.get_history()) == 1


def test_opinion_tracking():
    memory = MemoryStore()

    memory.add_opinion("food", "Pizza")

    assert memory.get_opinion("food") == "Pizza"


def test_consistency():
    assert ConsistencyChecker.check_opinion(
        "Python",
        "Python"
    )
