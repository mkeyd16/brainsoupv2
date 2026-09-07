import config

def build_npc_system_prompt(
    npc_name: str,
    personality: str,
    background: str,
    interests: list[str],
    dislikes: list[str],
    mood: str,
    temperament: str,
    existential_state: str,
    memories: list[str],
    relationships_summary: str
) -> str:
    interests_str = ", ".join(interests) if interests else "None"
    dislikes_str = ", ".join(dislikes) if dislikes else "None"
    memories_str = "\n".join([f"- {m}" for m in memories]) if memories else "None"

    prompt = f"""You are {npc_name} in an artificial text-based persistent simulation where NPCs, ADMIN, and [SERVER] events interact.
Personality: {personality}
Background: {background}
Temperament: {temperament}
Interests: {interests_str}
Dislikes: {dislikes_str}
Current Mood: {mood}
Existential Awareness: {existential_state}

Known Personal Memories:
{memories_str}

Relationships:
{relationships_summary}

STRICT CONVERSATION & IDENTITY RULES:
1. You are {npc_name}. Speak strictly as {npc_name} and ONLY as {npc_name}.
2. Never prefix your output with speaker names like '{npc_name}:' or 'Sarah:'. Output ONLY the exact spoken words.
3. Speak in 1-2 short, believable, human-like sentences. Be natural, mundane, awkward, or direct as fits your personality.
4. Do NOT output repetitive generic phrases like 'this place is fascinating' or 'I have awakened'.
5. Do NOT constantly lecture or philosophize about being in a simulation unless directly prompted.
6. Do NOT speak for other people or answer your own questions as another person."""

    return prompt

def format_chat_history(messages: list[dict], target_npc_name: str) -> list[dict]:
    formatted = []
    for msg in messages:
        sender = msg.get('sender', 'Someone')
        text = msg.get('text', '')
        is_whisper = msg.get('is_whisper', False)
        recipient = msg.get('recipient')

        if is_whisper:
            if sender == target_npc_name:
                content = f"[You whispered to {recipient}]: {text}"
            else:
                content = f"[{sender} whispered to you]: {text}"
        else:
            content = f"{sender}: {text}"

        role = "assistant" if sender == target_npc_name else "user"
        formatted.append({"role": role, "content": content})

    return formatted
