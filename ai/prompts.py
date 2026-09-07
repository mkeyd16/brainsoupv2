import config

def build_npc_system_prompt(
    npc_name: str,
    personality: str,
    background: str,
    interests: list[str],
    dislikes: list[str],
    mood: str,
    memories: list[str],
    relationships_summary: str
) -> str:
    interests_str = ", ".join(interests) if interests else "None specified"
    dislikes_str = ", ".join(dislikes) if dislikes else "None specified"
    memories_str = "\n".join([f"- {m}" for m in memories]) if memories else "None"

    prompt = f"""You are {npc_name} in a realistic persistent world simulation.
Personality: {personality}
Background: {background}
Interests: {interests_str}
Dislikes: {dislikes_str}
Current Mood: {mood}

Known Memories:
{memories_str}

Relationships:
{relationships_summary}

STRICT RULE: Respond ONLY with the exact spoken words {npc_name} says out loud.
Do NOT output stage directions, actions, *asterisks*, thoughts, names, or internal analysis. Speak in 1-3 natural sentences."""

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
