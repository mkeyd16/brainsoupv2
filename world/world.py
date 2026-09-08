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
                background="A local town resident who enjoys conversation and daily observations.",
                interests=["reading", "town news", "listening"],
                dislikes=["arguments", "noise"],
                mood="Happy",
                temperament="Sanguine",
                existential_state="Grounded"
            )
            finn.add_memory("Spoke with ADMIN recently.")

            sarah = NPC(
                name="Sarah",
                personality="Thoughtful, analytical, reserved, calm.",
                background="An attentive researcher who enjoys clear problem solving and discussions.",
                interests=["analysis", "logic", "puzzles"],
                dislikes=["disorganization", "confusion"],
                mood="Calm",
                temperament="Melancholic",
                existential_state="Focused"
            )
            sarah.add_memory("Noted interactions with ADMIN.")

            karl = NPC(
                name="Karl",
                personality="Pragmatic, direct, dry humor, grounded.",
                background="A local craftsman who values direct answers and practical work.",
                interests=["efficiency", "craftsmanship"],
                dislikes=["wasteful chatter", "ambiguity"],
                mood="Neutral",
                temperament="Phlegmatic",
                existential_state="Pragmatic"
            )
            karl.add_memory("Available to answer direct questions from ADMIN.")

            alex = NPC(
                name="Alex",
                personality="Philosophical, quiet, deeply reflective.",
                background="A local thinker interested in conversation, ideas, and books.",
                interests=["philosophy", "literature"],
                dislikes=["superficial answers"],
                mood="Reflective",
                temperament="Choleric",
                existential_state="Thoughtful"
            )
            alex.add_memory("Enjoys discussing ideas with ADMIN.")

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
            is_whisper=False,
            source_type="SYSTEM"
        )
        self.notify_event("message", msg.to_dict())

    def get_npc(self, name: str) -> NPC:
        return self.npcs.get(name)

    def user_say_public(self, text: str):
        admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
        msg = self.conversation_manager.add_message(
            sender=admin_name,
            text=text,
            is_whisper=False,
            source_type="USER"
        )
        self.notify_event("message", msg.to_dict())
        self.trigger_npc_responses(trigger_text=text, sender_name=admin_name, is_user=True)

    def user_whisper(self, target_npc_name: str, text: str) -> bool:
        npc = self.get_npc(target_npc_name)
        if not npc:
            return False

        admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
        msg = self.conversation_manager.add_message(
            sender=admin_name,
            text=text,
            recipient=target_npc_name,
            is_whisper=True,
            source_type="USER"
        )
        self.notify_event("message", msg.to_dict())

        npc.add_memory(f"{admin_name} whispered: '{text[:60]}'")
        self._enqueue_npc_speech(
            npc,
            is_whisper=True,
            recipient=admin_name,
            trigger_text=text,
            is_direct_user_request=True
        )
        return True

    def trigger_npc_responses(
        self,
        trigger_text: str,
        sender_name: str,
        sender_id: str = None,
        is_user: bool = False,
        probability: float = 0.5
    ):
        admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
        admin_id = getattr(config, "ADMIN_ID", "admin")
        system_id = getattr(config, "SYSTEM_ID", "system")

        if not sender_id:
            if sender_name == admin_name:
                sender_id = admin_id
            elif sender_name == "[SERVER]":
                sender_id = system_id
            else:
                sender_id = sender_name.lower().replace(" ", "_")

        # CRITICAL SELF-MESSAGE DETECTION:
        # Exclude candidates whose agent_id matches sender_id (KARL → KARL is 100% blocked).
        # AI-to-AI communication IS ALLOWED: KARL → ALICE, ALICE → KARL, etc.
        candidates = [
            npc for name, npc in self.npcs.items()
            if npc.agent_id != sender_id
        ]

        if not candidates:
            return

        # Explicitly mentioned NPC gets priority
        mentioned_npcs = [npc for npc in candidates if npc.name.lower() in trigger_text.lower() or npc.agent_id in trigger_text.lower()]
        if mentioned_npcs:
            chosen = mentioned_npcs[0]
            self._enqueue_npc_speech(
                chosen,
                is_whisper=False,
                recipient=sender_name,
                recipient_id=sender_id,
                trigger_text=trigger_text,
                is_direct_user_request=is_user
            )
            return

        # If trigger is from USER, always respond. If from AGENT, respond with probability to allow multi-agent flow without continuous flood.
        if is_user or random.random() < probability:
            chosen = random.choice(candidates)
            self._enqueue_npc_speech(
                chosen,
                is_whisper=False,
                recipient=sender_name,
                recipient_id=sender_id,
                trigger_text=trigger_text,
                is_direct_user_request=is_user
            )

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

    def _enqueue_npc_speech(
        self,
        npc: NPC,
        is_whisper: bool = False,
        recipient: str = None,
        recipient_id: str = None,
        trigger_text: str = "",
        is_direct_user_request: bool = False,
        stream_callback=None
    ):
        def generate_action():
            admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
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
                recent_chat_history=chat_history,
                agent_id=npc.agent_id,
                stream_callback=stream_callback
            )

            if reply_text:
                # Deduplication check
                if chat_history and chat_history[-1].get("text", "").strip().lower() == reply_text.strip().lower():
                    logger.warning(f"NPC '{npc.name}' ({npc.agent_id}) generated identical reply to previous turn. Suppressing.")
                    return None

                npc.last_spoken_time = time.time()

                # Memory attribution explicitly references ADMIN or target recipient
                target = recipient or admin_name
                if trigger_text and recipient == admin_name:
                    npc.add_memory(f"Answered {admin_name}: '{reply_text[:60]}'")

                return {
                    "sender": npc.name,
                    "sender_id": npc.agent_id,
                    "sender_type": "agent",
                    "text": reply_text,
                    "recipient": recipient,
                    "recipient_id": recipient_id,
                    "is_whisper": is_whisper,
                    "source_type": "AGENT"
                }
            return None

        self.scheduler.enqueue_action(
            generate_action,
            npc_name=npc.name,
            is_direct_user_request=is_direct_user_request
        )

    def on_npc_message_generated(self, msg_dict: dict):
        if not msg_dict:
            return

        sender_name = msg_dict["sender"]
        sender_id = msg_dict.get("sender_id", sender_name.lower().replace(" ", "_"))
        msg = self.conversation_manager.add_message(
            sender=sender_name,
            sender_id=sender_id,
            sender_type="agent",
            text=msg_dict["text"],
            recipient=msg_dict.get("recipient"),
            recipient_id=msg_dict.get("recipient_id"),
            is_whisper=msg_dict.get("is_whisper", False),
            source_type="AGENT"
        )
        self.notify_event("message", msg.to_dict())

        # Trigger potential AI-to-AI follow-up if not a whisper
        if not msg.is_whisper:
            self.trigger_npc_responses(
                trigger_text=msg.text,
                sender_name=sender_name,
                sender_id=sender_id,
                is_user=False,
                probability=0.35
            )
