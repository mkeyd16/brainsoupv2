import time
import logging
import uuid
import config

logger = logging.getLogger("wrld.world.conversation")

class Message:
    def __init__(
        self,
        sender: str,
        text: str,
        sender_id: str = None,
        sender_type: str = None,  # "admin", "agent", or "system"
        recipient: str = None,
        recipient_id: str = None,
        timestamp: float = None,
        msg_id: str = None,
        source_type: str = None,  # Legacy alias ("USER", "AGENT", "SYSTEM")
        processed: bool = False
    ):
        admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
        admin_id = getattr(config, "ADMIN_ID", "admin")
        system_id = getattr(config, "SYSTEM_ID", "system")

        self.id = msg_id or str(uuid.uuid4())
        self.sender = sender
        self.text = text
        self.recipient = recipient
        self.recipient_id = recipient_id or (recipient.lower().replace(" ", "_") if recipient else None)
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.processed = processed

        # Resolve sender_id and sender_type consistently
        if sender_id:
            self.sender_id = sender_id
        elif sender == admin_name:
            self.sender_id = admin_id
        elif sender == "[SERVER]":
            self.sender_id = system_id
        else:
            self.sender_id = sender.lower().replace(" ", "_")

        if sender_type:
            self.sender_type = sender_type
        elif self.sender_id == admin_id or sender == admin_name:
            self.sender_type = "admin"
        elif self.sender_id == system_id or sender == "[SERVER]":
            self.sender_type = "system"
        else:
            self.sender_type = "agent"

        # Legacy source_type support
        self.source_type = source_type or self.sender_type.upper()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "sender_id": self.sender_id,
            "sender_type": self.sender_type,
            "text": self.text,
            "recipient": self.recipient,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "source_type": self.source_type,
            "processed": self.processed
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        admin_name = getattr(config, "ADMIN_NAME", "ADMIN")
        admin_id = getattr(config, "ADMIN_ID", "admin")
        sender = data.get("sender", "Unknown")
        sender_id = data.get("sender_id") or (admin_id if sender == admin_name else (data.get("source_type", "").lower() if sender == "[SERVER]" else sender.lower().replace(" ", "_")))
        sender_type = data.get("sender_type") or ("admin" if sender == admin_name else ("system" if sender == "[SERVER]" else "agent"))

        return cls(
            msg_id=data.get("id"),
            sender=sender,
            sender_id=sender_id,
            sender_type=sender_type,
            text=data.get("text", ""),
            recipient=data.get("recipient"),
            recipient_id=data.get("recipient_id"),
            timestamp=data.get("timestamp"),
            source_type=data.get("source_type"),
            processed=data.get("processed", False)
        )

class ConversationManager:
    def __init__(self, max_history: int = config.MAX_PROMPT_HISTORY * 2):
        self.history: list[Message] = []
        self.max_history = max_history
        self.last_speaker = None
        self.last_speaker_id = None

    def add_message(
        self,
        sender: str,
        text: str,
        sender_id: str = None,
        sender_type: str = None,
        recipient: str = None,
        recipient_id: str = None,
        source_type: str = None
    ) -> Message:
        clean_text = text.strip()

        # Check for duplicate consecutive messages to prevent echo/looping
        if self.history:
            last_msg = self.history[-1]
            if last_msg.sender == sender and last_msg.text.strip().lower() == clean_text.lower():
                logger.warning(f"Prevented committing duplicate consecutive message from '{sender}': {clean_text}")
                return last_msg

        msg = Message(
            sender=sender,
            sender_id=sender_id,
            sender_type=sender_type,
            text=clean_text,
            recipient=recipient,
            recipient_id=recipient_id,
            source_type=source_type
        )
        self.history.append(msg)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        self.last_speaker = sender
        self.last_speaker_id = msg.sender_id
        return msg

    def get_visible_history_for_participant(self, participant_name: str, limit: int = config.MAX_PROMPT_HISTORY) -> list[dict]:
        visible = [msg.to_dict() for msg in reversed(self.history[:limit])]
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
