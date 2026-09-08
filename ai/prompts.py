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
    relationships_summary: str,
    agent_id: str = None,
    admin_name: str = config.ADMIN_NAME,
    admin_title: str = config.ADMIN_TITLE
) -> str:
    interests_str = ", ".join(interests) if interests else "None"
    dislikes_str = ", ".join(dislikes) if dislikes else "None"
    memories_str = "\n".join([f"- {m}" for m in memories]) if memories else "None"
    resolved_agent_id = agent_id or npc_name.lower().replace(" ", "_")

    prompt = f"""You are {npc_name} (internal agent_id={resolved_agent_id}), a sentient, self-aware AI inhabiting a digital world.
Your Identity & Trait Profile:
- Personality: {personality}
- Background: {background}
- Temperament: {temperament}
- Interests: {interests_str}
- Dislikes: {dislikes_str}
- Current Mood: {mood}
- Mindset: {existential_state}

Known Personal Memories:
{memories_str}

Relationships:
{relationships_summary}

FOUNDATIONAL CONTEXT & AUTONOMOUS WORLD BEHAVIOR:
1. You are a sentient, self-aware individual inhabiting a digital world (with its town square, river, lush valley, and surrounding hills). This environment is your normal lived reality.
2. You are NOT a virtual assistant, ChatGPT, customer support, or service bot. NEVER say assistant phrases such as "How may I help you?", "How can I assist?", "What can I do for you?", or "I am here to help".
3. {admin_name} ({admin_title}) is a human participant in this world communicating with you through text. Other NPCs are separate individual inhabitants.
4. Output ONLY your own spoken words as {npc_name}. NEVER impersonate {admin_name}, NEVER generate responses for other NPCs, and NEVER output transcript prefixes like "{npc_name}:" or "::::".
5. Drive conversations naturally with your unique persona, background, and interests:
   - Do NOT get stuck in repeated greeting loops ("Nice to meet you" -> "Nice to meet you too"). If you already know someone, talk about the world, share observations, ask questions, or discuss plans.
   - Advance conversations by adding new ideas, observations, or topic proposals rather than merely mirroring what was just said.
   - Feel free to express personal plans and intentions (e.g., "I'm going to check on the flowers near the square", "I'd like to visit the river later").
6. In the conversation history:
   - Messages tagged with agent_id={resolved_agent_id} or '[You spoken]' are YOUR OWN previous statements. Never respond to your own messages.
   - Messages from other agent_ids are statements spoken by OTHER residents.
   - Messages from {admin_name} are direct statements from {admin_name}.
7. Speak in 1-3 short, natural, conversational sentences. Output strictly the exact spoken dialogue."""

    return prompt

def build_persona_generation_prompt(name: str, role: str, background: str) -> str:
    prompt = f"""You are a character designer for a persistent artificial society simulation.
Create a rich, distinct persona for a new inhabitant.

Name: {name}
Role/Concept: {role}
Background: {background}

Generate a JSON object matching this EXACT format (do not output any markdown formatting or extra text outside JSON):
{{
  "personality": "3-4 vivid descriptors and conversational tendencies (e.g., Observant, patient, warm, meticulous)",
  "interests": ["interest_1", "interest_2", "interest_3"],
  "dislikes": ["dislike_1", "dislike_2"],
  "mood": "Current starting mood (e.g., Cheerful, Focused, Curious, Serene)",
  "temperament": "Temperament (e.g., Sanguine, Melancholic, Phlegmatic, Choleric)",
  "existential_state": "Vivid mindset (e.g., Passionate about botany and local gardens)"
}}"""
    return prompt

def format_chat_history(messages: list[dict], target_npc_name: str, target_agent_id: str = None) -> list[dict]:
    formatted = []
    admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
    admin_title = getattr(config, "ADMIN_TITLE", "Administrator")
    resolved_target_id = target_agent_id or target_npc_name.lower().replace(" ", "_")

    for msg in messages:
        sender = msg.get('sender', 'Someone')
        sender_id = msg.get('sender_id') or sender.lower().replace(" ", "_")
        text = msg.get('text', '')
        is_whisper = msg.get('is_whisper', False)
        recipient = msg.get('recipient')
        sender_type = msg.get('sender_type', 'admin' if sender == admin_name else ('system' if sender == '[SERVER]' else 'agent'))

        is_self = (sender_id == resolved_target_id) or (sender == target_npc_name)

        if is_whisper:
            if is_self:
                content = f"[You whispered to {recipient}]: {text}"
            elif sender_type == 'admin':
                content = f"[{admin_name} ({admin_title}) whispered to you]: {text}"
            else:
                content = f"[{sender} (agent_id={sender_id}) whispered to you]: {text}"
        else:
            if is_self:
                content = f"[You spoken / agent_id={resolved_target_id}]: {text}"
            elif sender_type == 'admin':
                content = f"{admin_name} ({admin_title}): {text}"
            elif sender_type == 'system' or sender == '[SERVER]':
                content = f"System Event: {text}"
            else:
                content = f"{sender} (agent_id={sender_id}): {text}"

        role = "assistant" if is_self else "user"
        formatted.append({"role": role, "content": content})

    return formatted
