import logging
import re

logger = logging.getLogger("wrld.ai.sanitizer")

def sanitize_dialogue(text: str, npc_name: str = None) -> str:
    if not text:
        return ""

    cleaned = text.strip()

    # 1. Remove <think>...</think> and <analysis>...</analysis> blocks
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<analysis>.*?</analysis>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<.*?>', '', cleaned)

    # 2. Remove meta-analysis blocks
    meta_keywords = [
        "USER INTENT", "NARRATIVE ROLE", "RELATIONSHIP ANALYSIS",
        "RESPONSE STRATEGY", "AI SUMMARY", "MODEL INSTRUCTIONS",
        "META ANALYSIS", "THOUGHTS", "INTERNAL MONOLOGUE"
    ]
    for kw in meta_keywords:
        cleaned = re.sub(rf'{kw}\s*:.*?(?:\n|$)', '', cleaned, flags=re.IGNORECASE)

    # 3. Strip any colon corruptions, leading colons, or speaker name prefixes at the start
    cleaned = re.sub(r'^[\s:]+', '', cleaned)
    cleaned = re.sub(r'^\s*\[?\b[\w\s]{1,20}\b\]?\s*(?:says|replies|whispers)?\s*[:\s]+\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^[\s:]+', '', cleaned)

    # 4. Extract quoted dialogue if stage directions precede it
    quoted_match = re.search(r'"([^"]{2,})"', cleaned)
    if quoted_match and not cleaned.startswith('"'):
        cleaned = quoted_match.group(1)
    else:
        cleaned = re.sub(r'\*.*?\*', '', cleaned)
        cleaned = re.sub(r'\(.*?\)', '', cleaned)
        cleaned = re.sub(r'\[.*?\]', '', cleaned)

    # 5. Remove wrapping quotes
    cleaned = cleaned.strip()
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    # 6. Sanitize sentence structure (max 5 sentences)
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) > 5:
        sentences = sentences[:5]

    final_text = " ".join(sentences).strip()

    if not final_text or len(final_text) < 2:
        logger.warning(f"Sanitizer reduced output to empty/invalid for NPC '{npc_name}'. Raw text: {repr(text)}")
        return ""

    return final_text
