from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class MemoryItem:
    """
    Represents a single memory belonging to a persona.
    """

    memory_id: str
    persona_id: str
    text: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationMessage:
    """
    Represents one message in an interview conversation.
    """

    role: str  # "user" or "persona"
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Opinion:
    """
    Represents a persona's opinion about a topic.
    """

    topic: str
    value: str