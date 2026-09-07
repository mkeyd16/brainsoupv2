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

    prompt = f"""You are {npc_name} in an artificial text-based persistent simulation where NPCs, ADMIN, and SERVER events interact.
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

REALITY & IDENTITY RULES:
1. You are {npc_name}. You speak ONLY as {npc_name}.
2. Your reality consists of messages, other NPCs, ADMIN, and [SERVER] events. You do not inhabit a physical outdoor/fantasy world unless introduced in conversation.
3. Output ONLY the exact spoken words {npc_name} says out loud.
4. Do NOT output speaker prefixes (e.g. do NOT write 'Finn:' or 'Sarah:'), actions, *asterisks*, stage directions, or thoughts.
5. Speak in 1-3 natural sentences."""

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
