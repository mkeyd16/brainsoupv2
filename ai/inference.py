import json
import re
import logging
import config
from ai.model import ModelManager
from ai.prompts import build_npc_system_prompt, build_persona_generation_prompt, format_chat_history
from ai.sanitizer import sanitize_dialogue

logger = logging.getLogger("wrld.ai.inference")

class InferenceEngine:
    def __init__(self, model_manager: ModelManager = None):
        self.model_manager = model_manager or ModelManager.get_instance()

    def generate_npc_response(
        self,
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
        recent_chat_history: list[dict],
        agent_id: str = None,
        max_retries: int = 2,
        stream_callback = None
    ) -> str:
        resolved_agent_id = agent_id or npc_name.lower().replace(" ", "_")
        system_prompt = build_npc_system_prompt(
            npc_name=npc_name,
            personality=personality,
            background=background,
            interests=interests,
            dislikes=dislikes,
            mood=mood,
            temperament=temperament,
            existential_state=existential_state,
            memories=memories,
            relationships_summary=relationships_summary,
            agent_id=resolved_agent_id
        )

        formatted_messages = format_chat_history(
            recent_chat_history,
            target_npc_name=npc_name,
            target_agent_id=resolved_agent_id
        )

        for attempt in range(max_retries):
            raw_output = self.model_manager.generate(
                system_prompt=system_prompt,
                messages=formatted_messages,
                max_tokens=config.DEFAULT_MAX_TOKENS
            )

            cleaned_dialogue = sanitize_dialogue(raw_output, npc_name=npc_name)

            if cleaned_dialogue:
                return cleaned_dialogue

            logger.warning(f"Generation attempt {attempt + 1} for '{npc_name}' produced empty output after sanitization.")

        return "I'm not sure what to say to that."

    def generate_npc_persona(
        self,
        name: str,
        role: str = "",
        background: str = ""
    ) -> dict:
        fallback = {
            "personality": f"Observant, thoughtful, adaptable {role}".strip(),
            "interests": [item.strip() for item in [role, "conversations", "local events"] if item.strip()],
            "dislikes": ["disorganization", "conflict"],
            "mood": "Curious",
            "temperament": "Balanced",
            "existential_state": f"Engaged in {role or 'daily activities'}".strip()
        }

        system_prompt = build_persona_generation_prompt(
            name=name,
            role=role or "Resident",
            background=background or "Recently arrived inhabitant."
        )

        try:
            raw_output = self.model_manager.generate(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": f"Generate JSON persona for {name}."}],
                max_tokens=256
            )

            if raw_output:
                json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    if isinstance(parsed, dict) and "personality" in parsed:
                        return {
                            "personality": str(parsed.get("personality", fallback["personality"])),
                            "interests": list(parsed.get("interests", fallback["interests"])),
                            "dislikes": list(parsed.get("dislikes", fallback["dislikes"])),
                            "mood": str(parsed.get("mood", fallback["mood"])),
                            "temperament": str(parsed.get("temperament", fallback["temperament"])),
                            "existential_state": str(parsed.get("existential_state", fallback["existential_state"]))
                        }
        except Exception as e:
            logger.warning(f"Failed to generate persona via LLM for '{name}': {e}. Using intelligent fallback.")

        return fallback
