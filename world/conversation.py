import time
import logging
import config

logger = logging.getLogger("wrld.world.conversation")

class Message:
    def __init__(self, sender: str, text: str, recipient: str = None, is_whisper: bool = False, timestamp: float = None):
        self.sender = sender
        self.text = text
        self.recipient = recipient
        self.is_whisper = is_whisper
        self.timestamp = timestamp if timestamp is not None else time.time()

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "text": self.text,
            "recipient": self.recipient,
            "is_whisper": self.is_whisper,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
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

    def add_message(self, sender: str, text: str, recipient: str = None, is_whisper: bool = False) -> Message:
        msg = Message(sender=sender, text=text, recipient=recipient, is_whisper=is_whisper)
        self.history.append(msg)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
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
        self.history = [Message.from_dict(m) for m in data_list if isinstance(m, dict)]
