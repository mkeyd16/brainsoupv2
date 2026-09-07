import random
import time
import logging
import config
from world.npc import NPC
from world.conversation import ConversationManager
from world.scheduler import SimulationScheduler
from ai.inference import InferenceEngine

logger = logging.getLogger("wrld.world.engine")

class World:
    def __init__(self, inference_engine: InferenceEngine = None):
        self.npcs: dict[str, NPC] = {}
        self.conversation_manager = ConversationManager()
        self.scheduler = SimulationScheduler(cooldown_seconds=config.MESSAGE_COOLDOWN_SECONDS)
        self.inference_engine = inference_engine or InferenceEngine()
        self.scheduler.set_message_callback(self.on_npc_message_generated)
        self.user_name = "User"
        self.event_listeners = []
        self._setup_default_npcs_if_empty()

    def _setup_default_npcs_if_empty(self):
        if not self.npcs:
            finn = NPC(
                name="Finn",
                personality="Cheerful, curious, outgoing, loves storytelling and exploring.",
                background="A local resident who spent years wandering nearby trails.",
                interests=["gardening", "stargazing", "exploring"],
                dislikes=["rain", "arguing"],
                mood="Happy"
            )
            finn.add_memory("Enjoys taking morning walks around town.")

            sarah = NPC(
                name="Sarah",
                personality="Thoughtful, analytical, reserved, avid book reader.",
                background="Runs the local book corner and loves discussing quiet topics.",
                interests=["reading", "tea", "puzzles"],
                dislikes=["loud noises", "disorganization"],
                mood="Calm"
            )
            sarah.add_memory("Loves brewing herbal tea while reading books.")

            self.add_npc(finn)
            self.add_npc(sarah)

            finn.relationships.modify_score("Sarah", 25, "Friendly neighbor")
            sarah.relationships.modify_score("Finn", 25, "Passes by the shop")

    def add_event_listener(self, listener_func):
        self.event_listeners.append(listener_func)

    def notify_event(self, event_type: str, data: dict):
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")

    def add_npc(self, npc: NPC) -> bool:
        if npc.name in self.npcs:
            return False
        self.npcs[npc.name] = npc
        self.notify_event("npc_added", {"npc": npc.name})
        return True

    def remove_npc(self, name: str) -> bool:
        if name in self.npcs:
            del self.npcs[name]
            self.notify_event("npc_removed", {"name": name})
            return True
        return False

    def get_npc(self, name: str) -> NPC:
        return self.npcs.get(name)

    def user_say_public(self, text: str):
        msg = self.conversation_manager.add_message(
            sender=self.user_name,
            text=text,
            is_whisper=False
        )
        self.notify_event("message", msg.to_dict())
        self.trigger_npc_responses(trigger_text=text, sender_name=self.user_name)

    def user_whisper(self, target_npc_name: str, text: str) -> bool:
        npc = self.get_npc(target_npc_name)
        if not npc:
            return False

        msg = self.conversation_manager.add_message(
            sender=self.user_name,
            text=text,
            recipient=target_npc_name,
            is_whisper=True
        )
        self.notify_event("message", msg.to_dict())

        self._enqueue_npc_speech(npc, is_whisper=True, recipient=self.user_name, trigger_text=text)
        return True

    def trigger_npc_responses(self, trigger_text: str, sender_name: str, probability: float = 0.5):
        """
        Determines which NPCs respond to a public message.
        """
        for name, npc in self.npcs.items():
            if name == sender_name:
                continue

            is_mentioned = name.lower() in trigger_text.lower()
            should_respond = is_mentioned or (random.random() < probability)

            if should_respond:
                self._enqueue_npc_speech(npc, is_whisper=False, trigger_text=trigger_text)

    def autonomous_tick(self):
        if not self.npcs or self.scheduler.is_paused:
            return

        now = time.time()
        candidates = [
            npc for npc in self.npcs.values()
            if (now - npc.last_spoken_time) > 20.0
        ]

        if candidates and random.random() < 0.2:
            chosen = random.choice(candidates)
            recent_vis = self.conversation_manager.get_visible_history_for_participant(chosen.name)
            last_text = recent_vis[-1]["text"] if recent_vis else ""
            self._enqueue_npc_speech(chosen, is_whisper=False, trigger_text=last_text)

    def _enqueue_npc_speech(self, npc: NPC, is_whisper: bool = False, recipient: str = None, trigger_text: str = ""):
        def generate_action():
            memories = npc.get_relevant_memories(trigger_text)
            rel_summary = npc.get_relationship_summary()
            chat_history = self.conversation_manager.get_visible_history_for_participant(npc.name)

            reply_text = self.inference_engine.generate_npc_response(
                npc_name=npc.name,
                personality=npc.personality,
                background=npc.background,
                interests=npc.interests,
                dislikes=npc.dislikes,
                mood=npc.mood,
                memories=memories,
                relationships_summary=rel_summary,
                recent_chat_history=chat_history
            )

            if reply_text:
                npc.last_spoken_time = time.time()
                npc.add_memory(f"Said to {recipient or 'everyone'}: {reply_text[:60]}")
                return {
                    "sender": npc.name,
                    "text": reply_text,
                    "recipient": recipient,
                    "is_whisper": is_whisper
                }
            return None

        self.scheduler.enqueue_action(generate_action, npc_name=npc.name)

    def on_npc_message_generated(self, msg_dict: dict):
        if not msg_dict:
            return
        msg = self.conversation_manager.add_message(
            sender=msg_dict["sender"],
            text=msg_dict["text"],
            recipient=msg_dict.get("recipient"),
            is_whisper=msg_dict.get("is_whisper", False)
        )
        self.notify_event("message", msg.to_dict())

        # When an NPC generates a public message, trigger other NPCs with low probability (20%) to avoid endless chatter loop
        if not msg.is_whisper:
            self.trigger_npc_responses(trigger_text=msg.text, sender_name=msg.sender, probability=0.2)
