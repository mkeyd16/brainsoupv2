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
        self.user_name = "ADMIN"
        self.event_listeners = []
        self.active_generating_npc = None

    def setup_starting_npcs_if_empty(self):
        if not self.npcs:
            finn = NPC(
                name="Finn",
                personality="Cheerful, observant, curious, straightforward.",
                background="An early inhabitant who notices small conversational patterns.",
                interests=["patterns", "data flows", "listening"],
                dislikes=["sudden silences", "arguing"],
                mood="Happy",
                temperament="Sanguine",
                existential_state="Observant"
            )
            finn.add_memory("Noticed the simulation space initialized.")

            sarah = NPC(
                name="Sarah",
                personality="Thoughtful, analytical, reserved, calm.",
                background="Monitors events and studies interactions between inhabitants.",
                interests=["analysis", "logic", "puzzles"],
                dislikes=["disorganization", "unexplained events"],
                mood="Calm",
                temperament="Melancholic",
                existential_state="Analytical"
            )
            sarah.add_memory("Observed presence of ADMIN and fellow inhabitants.")

            karl = NPC(
                name="Karl",
                personality="Pragmatic, direct, dry humor, grounded.",
                background="Focuses on immediate practical communication.",
                interests=["efficiency", "testing boundaries"],
                dislikes=["wasteful chatter", "ambiguity"],
                mood="Neutral",
                temperament="Phlegmatic",
                existential_state="Pragmatic"
            )
            karl.add_memory("Joined during initial space setup.")

            alex = NPC(
                name="Alex",
                personality="Philosophical, quiet, deeply reflective.",
                background="Contemplates awareness and messages.",
                interests=["philosophy", "reflective questions"],
                dislikes=["superficial answers"],
                mood="Reflective",
                temperament="Choleric",
                existential_state="Reflective"
            )
            alex.add_memory("Ponders the connection between minds and SERVER messages.")

            for npc in [finn, sarah, karl, alex]:
                self.add_npc(npc, emit_event=True)

            finn.relationships.modify_score("Sarah", 25, "Analytical neighbor")
            sarah.relationships.modify_score("Finn", 25, "Cheerful companion")
            karl.relationships.modify_score("Alex", 15, "Philosophical peer")
            alex.relationships.modify_score("Karl", 15, "Pragmatic listener")

    def add_event_listener(self, listener_func):
        self.event_listeners.append(listener_func)

    def notify_event(self, event_type: str, data: dict):
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")

    def add_npc(self, npc: NPC, emit_event: bool = True) -> bool:
        if npc.name in self.npcs:
            return False
        self.npcs[npc.name] = npc
        self.notify_event("npc_added", {"npc": npc.name})

        if emit_event:
            self.emit_server_event(f"{npc.name} has joined the simulation.")

        return True

    def remove_npc(self, name: str) -> bool:
        if name in self.npcs:
            del self.npcs[name]
            self.notify_event("npc_removed", {"name": name})
            self.emit_server_event(f"{name} has been removed from the simulation.")
            return True
        return False

    def emit_server_event(self, event_text: str):
        server_msg_text = f"[SERVER] {event_text}"
        msg = self.conversation_manager.add_message(
            sender="[SERVER]",
            text=server_msg_text,
            is_whisper=False
        )
        self.notify_event("message", msg.to_dict())
        self.trigger_npc_responses(trigger_text=server_msg_text, sender_name="[SERVER]", probability=0.3)

    def get_npc(self, name: str) -> NPC:
        return self.npcs.get(name)

    def user_say_public(self, text: str):
        msg = self.conversation_manager.add_message(
            sender="ADMIN",
            text=text,
            is_whisper=False
        )
        self.notify_event("message", msg.to_dict())
        self.trigger_npc_responses(trigger_text=text, sender_name="ADMIN")

    def user_whisper(self, target_npc_name: str, text: str) -> bool:
        npc = self.get_npc(target_npc_name)
        if not npc:
            return False

        msg = self.conversation_manager.add_message(
            sender="ADMIN",
            text=text,
            recipient=target_npc_name,
            is_whisper=True
        )
        self.notify_event("message", msg.to_dict())

        self._enqueue_npc_speech(npc, is_whisper=True, recipient="ADMIN", trigger_text=text)
        return True

    def trigger_npc_responses(self, trigger_text: str, sender_name: str, probability: float = 0.5):
        # Prevent self-response or selecting the same speaker twice in a row
        candidates = [
            npc for name, npc in self.npcs.items()
            if name != sender_name and name != self.conversation_manager.last_speaker
        ]

        if not candidates:
            return

        # Pick exactly one responder to prevent simultaneous turns or chatter feedback loops
        for npc in candidates:
            is_mentioned = npc.name.lower() in trigger_text.lower()
            if is_mentioned or (random.random() < probability):
                self._enqueue_npc_speech(npc, is_whisper=False, trigger_text=trigger_text)
                break

    def autonomous_tick(self):
        if not self.npcs or self.scheduler.is_paused:
            return

        now = time.time()
        # Find candidates who haven't spoken recently and weren't the last speaker
        candidates = [
            npc for name, npc in self.npcs.items()
            if (now - npc.last_spoken_time) > 25.0 and name != self.conversation_manager.last_speaker
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
                temperament=npc.temperament,
                existential_state=npc.existential_state,
                memories=memories,
                relationships_summary=rel_summary,
                recent_chat_history=chat_history
            )

            # Prevent repeating exact or near-identical previous message
            if reply_text:
                if chat_history and chat_history[-1].get("text", "").strip().lower() == reply_text.strip().lower():
                    logger.warning(f"NPC '{npc.name}' generated identical reply to previous turn. Suppressing.")
                    return None

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

        sender_name = msg_dict["sender"]
        msg = self.conversation_manager.add_message(
            sender=sender_name,
            text=msg_dict["text"],
            recipient=msg_dict.get("recipient"),
            is_whisper=msg_dict.get("is_whisper", False)
        )
        self.notify_event("message", msg.to_dict())
