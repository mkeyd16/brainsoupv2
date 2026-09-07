import time
import logging
from memory.memory_store import MemoryStore
from memory.memory_retrieval import retrieve_relevant_memories
from world.relationships import Relationships

logger = logging.getLogger("wrld.world.npc")

class NPC:
    def __init__(
        self,
        name: str,
        personality: str,
        background: str,
        interests: list[str] = None,
        dislikes: list[str] = None,
        mood: str = "Neutral"
    ):
        self.name = name
        self.personality = personality
        self.background = background
        self.interests = interests or []
        self.dislikes = dislikes or []
        self.mood = mood
        self.memory_store = MemoryStore()
        self.relationships = Relationships()
        self.last_spoken_time = 0.0

    def add_memory(self, fact: str, importance: int = 1) -> bool:
        return self.memory_store.add_memory(fact, importance)

    def get_relevant_memories(self, query: str = "") -> list[str]:
        return retrieve_relevant_memories(self.memory_store, query)

    def get_relationship_summary(self) -> str:
        return self.relationships.get_summary_string()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "personality": self.personality,
            "background": self.background,
            "interests": self.interests,
            "dislikes": self.dislikes,
            "mood": self.mood,
            "memories": self.memory_store.to_list(),
            "relationships": self.relationships.to_dict(),
            "last_spoken_time": self.last_spoken_time
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NPC":
        npc = cls(
            name=data.get("name", "Unknown"),
            personality=data.get("personality", "Friendly"),
            background=data.get("background", "Local inhabitant"),
            interests=data.get("interests", []),
            dislikes=data.get("dislikes", []),
            mood=data.get("mood", "Neutral")
        )
        if "memories" in data:
            npc.memory_store.load_from_list(data["memories"])
        if "relationships" in data:
            npc.relationships.load_from_dict(data["relationships"])
        npc.last_spoken_time = data.get("last_spoken_time", 0.0)
        return npc
