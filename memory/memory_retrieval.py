import re
import config
from memory.memory_store import MemoryStore, MemoryItem

def retrieve_relevant_memories(
    memory_store: MemoryStore,
    query_text: str = "",
    top_k: int = config.MAX_PROMPT_MEMORIES
) -> list[str]:
    if not memory_store or not memory_store.memories:
        return []

    memories = memory_store.memories

    if not query_text:
        sorted_mems = sorted(memories, key=lambda m: (m.importance, m.timestamp), reverse=True)
        return [m.fact for m in sorted_mems[:top_k]]

    query_words = set(re.findall(r'\w{3,}', query_text.lower()))

    scored_mems = []
    for m in memories:
        fact_lower = m.fact.lower()
        match_count = sum(1 for word in query_words if word in fact_lower)
        score = (match_count * 5) + (m.importance * 2) + (m.timestamp / 1e10)
        scored_mems.append((score, m))

    scored_mems.sort(key=lambda x: x[0], reverse=True)
    selected = [item[1].fact for item in scored_mems[:top_k]]

    return selected
