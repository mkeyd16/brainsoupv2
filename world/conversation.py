import time
import logging
import uuid
import config

logger = logging.getLogger("wrld.world.conversation")

class Message:
    def __init__(self, sender: str, text: str, recipient: str = None, is_whisper: bool = False, timestamp: float = None, msg_id: str = None):
        self.id = msg_id or str(uuid.uuid4())
        self.sender = sender
        self.text = text
        self.recipient = recipient
        self.is_whisper = is_whisper
        self.timestamp = timestamp if timestamp is not None else time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "text": self.text,
            "recipient": self.recipient,
            "is_whisper": self.is_whisper,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            msg_id=data.get("id"),
            sender=data.get("sender", "Unknown"),
            text=data.get("text", ""),
            recipient=data.get("recipient"),
            is_whisper=data.get("is_whisper", False),
            timestamp=data.get("timestamp")
        )

class ConversationManager:
    def __init__(self, max_history: int = config.MAX_PROMPT_HISTORY * 2):
        self.history: list[Message] = []
        self.max_history = max_history
        self.last_speaker = None

    def add_message(self, sender: str, text: str, recipient: str = None, is_whisper: bool = False) -> Message:
        # Check for duplicate consecutive messages to prevent echo/looping
        clean_text = text.strip()
        if self.history:
            last_msg = self.history[-1]
            if last_msg.sender == sender and last_msg.text.strip().lower() == clean_text.lower():
                logger.warning(f"Prevented committing duplicate consecutive message from '{sender}': {clean_text}")
                return last_msg

        msg = Message(sender=sender, text=clean_text, recipient=recipient, is_whisper=is_whisper)
        self.history.append(msg)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self.last_speaker = sender
        return msg

    def get_visible_history_for_participant(self, participant_name: str, limit: int = config.MAX_PROMPT_HISTORY) -> list[dict]:
        visible = []
        for msg in reversed(self.history):
            if msg.is_whisper:
                if msg.sender == participant_name or msg.recipient == participant_name:
                    visible.append(msg.to_dict())
            else:
                visible.append(msg.to_dict())

            if len(visible) >= limit:
                break

        return list(reversed(visible))

    def to_list(self) -> list[dict]:
        return [m.to_dict() for m in self.history]

    def load_from_list(self, data_list: list[dict]):
        self.history = []
        seen_ids = set()
        for item in data_list:
            if isinstance(item, dict):
                msg = Message.from_dict(item)
                if msg.id not in seen_ids:
                    self.history.append(msg)
                    seen_ids.add(msg.id)
