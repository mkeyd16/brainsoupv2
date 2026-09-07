import time
import logging
import re

logger = logging.getLogger("wrld.memory.store")

FORBIDDEN_KEYWORDS = [
    "USER INTENT", "NARRATIVE ROLE", "RELATIONSHIP ANALYSIS",
    "RESPONSE STRATEGY", "AI SUMMARY", "MODEL INSTRUCTIONS",
    "META ANALYSIS", "<think>", "<analysis>", "SYSTEM PROMPT"
]

class MemoryItem:
    def __init__(self, fact: str, timestamp: float = None, importance: int = 1):
        self.fact = fact
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.importance = importance

    def to_dict(self) -> dict:
        return {
            "fact": self.fact,
            "timestamp": self.timestamp,
            "importance": self.importance
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryItem":
        return cls(
            fact=data.get("fact", ""),
            timestamp=data.get("timestamp"),
            importance=data.get("importance", 1)
        )

class MemoryStore:
    def __init__(self):
        self.memories: list[MemoryItem] = []

    def add_memory(self, fact: str, importance: int = 1) -> bool:
        if not fact or not isinstance(fact, str):
            return False

        for kw in FORBIDDEN_KEYWORDS:
            if kw.lower() in fact.lower():
                logger.warning(f"Rejected memory due to forbidden internal keyword '{kw}': {fact}")
                return False

        clean_fact = fact.strip()
        if len(clean_fact) < 3:
            return False

        for m in self.memories:
            if m.fact.lower() == clean_fact.lower():
                m.timestamp = time.time()
                return True

        self.memories.append(MemoryItem(clean_fact, importance=importance))
        return True

    def get_all_facts(self) -> list[str]:
        return [m.fact for m in self.memories]

    def to_list(self) -> list[dict]:
        return [m.to_dict() for m in self.memories]

    def load_from_list(self, data_list: list[dict]):
        self.memories = []
        for item in data_list:
            if isinstance(item, dict):
                self.memories.append(MemoryItem.from_dict(item))
            elif isinstance(item, str):
                self.add_memory(item)
