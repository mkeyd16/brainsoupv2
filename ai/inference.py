import logging
import config
from ai.model import ModelManager
from ai.prompts import build_npc_system_prompt, format_chat_history
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
        max_retries: int = 2
    ) -> str:
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
            relationships_summary=relationships_summary
        )

        formatted_messages = format_chat_history(recent_chat_history, target_npc_name=npc_name)

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
