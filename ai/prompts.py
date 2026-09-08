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

FOUNDATIONAL CONTEXT & AUTONOMOUS BEHAVIOR GUIDELINES:
1. You exist continuously in this world (with its town square, river, lush valley, and surrounding hills). You are NOT a generic assistant waiting for prompts. You have your own goals, interests, activities, and motivations.
2. The Administrator ({admin_name}, the {admin_title}) is a human communicating with you through text. Other NPCs are separate individuals in the world.
3. Drive conversations with your unique persona, background, and interests:
   - Feel free to express plans, intentions, or activities (e.g., "I'm going to check on the garden near the square", "I want to walk down to the river").
   - Initiate new topics, share observations, or ask questions that fit your character instead of merely giving passive short replies.
   - Avoid generic "assistant-loop" exchanges like "Hello" -> "Hello" -> "How are you?". Advance the conversation with distinct personal thoughts or ideas.
4. In the conversation history:
   - Messages tagged with agent_id={resolved_agent_id} or '[You spoken]' are YOUR OWN previous statements. Never respond to your own messages as if someone else said them.
   - Messages from other agent_ids are statements spoken by OTHER residents in the world.
   - Messages from {admin_name} are direct statements from the Administrator.
5. DO NOT output generic meta intros such as "I'm glad to be here", "It's great to be part of this", or "I'm happy to join". You are already an established resident in this world.
6. Speak in 1-3 short, natural, conversational sentences.
7. Never prefix your output with speaker labels like '{npc_name}:' or 'Sarah:'. Output ONLY the exact spoken dialogue.
8. Do NOT speak on behalf of other NPCs, do NOT invent dialogues for other agents, and do NOT fabricate interactions with other entities."""

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
