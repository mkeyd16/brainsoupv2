import logging

logger = logging.getLogger("wrld.world.relationships")

class RelationshipTier:
    STRANGER = "Stranger"
    ACQUAINTANCE = "Acquaintance"
    FRIEND = "Friend"
    CLOSE_FRIEND = "Close Friend"
    RIVAL = "Rival"

class Relationships:
    def __init__(self):
        self.relationships: dict[str, dict] = {}

    def get_tier(self, score: float) -> str:
        if score <= -30:
            return RelationshipTier.RIVAL
        elif score < 20:
            return RelationshipTier.STRANGER
        elif score < 50:
            return RelationshipTier.ACQUAINTANCE
        elif score < 80:
            return RelationshipTier.FRIEND
        else:
            return RelationshipTier.CLOSE_FRIEND

    def get_relationship(self, target_name: str) -> dict:
        if target_name not in self.relationships:
            self.relationships[target_name] = {"score": 0.0, "notes": ""}
        rel = self.relationships[target_name]
        rel["tier"] = self.get_tier(rel["score"])
        return rel

    def modify_score(self, target_name: str, delta: float, note: str = ""):
        rel = self.get_relationship(target_name)
        new_score = max(-100.0, min(100.0, rel["score"] + delta))
        rel["score"] = new_score
        if note:
            rel["notes"] = note
        rel["tier"] = self.get_tier(new_score)

    def get_summary_string(self) -> str:
        if not self.relationships:
            return "No prior relationships established."

        lines = []
        for name, data in self.relationships.items():
            tier = self.get_tier(data["score"])
            lines.append(f"- {name}: {tier}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return self.relationships

    def load_from_dict(self, data: dict):
        if isinstance(data, dict):
            self.relationships = data
