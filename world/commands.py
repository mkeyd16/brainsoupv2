import logging
from world.world import World
from world.npc import NPC
from storage.save_manager import SaveManager

logger = logging.getLogger("wrld.world.commands")

class CommandHandler:
    def __init__(self, world: World):
        self.world = world

    def execute_command(self, raw_command: str) -> str:
        if not raw_command.startswith("/"):
            return "Commands must start with '/'"

        parts = raw_command.strip().split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd == "/help":
            return self._help()
        elif cmd == "/save":
            filename = parts[1] if len(parts) > 1 else None
            return self._save(filename)
        elif cmd == "/load":
            filename = parts[1] if len(parts) > 1 else None
            return self._load(filename)
        elif cmd == "/pause":
            self.world.scheduler.pause()
            return "Simulation paused."
        elif cmd == "/resume":
            self.world.scheduler.resume()
            return "Simulation resumed."
        elif cmd == "/whisper":
            if len(parts) < 3:
                return "Usage: /whisper NPC_NAME MESSAGE"
            target_npc = parts[1]
            message = parts[2]
            success = self.world.user_whisper(target_npc, message)
            if success:
                return f"[Whisper sent to {target_npc}]: {message}"
            else:
                return f"NPC '{target_npc}' not found."
        elif cmd == "/npcs":
            return self._list_npcs()
        elif cmd == "/inspect":
            if len(parts) < 2:
                return "Usage: /inspect NPC_NAME"
            return self._inspect_npc(parts[1])
        elif cmd == "/create":
            if len(parts) < 2:
                return "Usage: /create NAME | PERSONALITY | BACKGROUND"
            args_str = raw_command[len("/create"):].strip()
            return self._create_npc(args_str)
        elif cmd == "/remove":
            if len(parts) < 2:
                return "Usage: /remove NPC_NAME"
            return self._remove_npc(parts[1])
        else:
            return f"Unknown command '{cmd}'. Type /help for available commands."

    def _help(self) -> str:
        return """Available Commands:
/help                     - Show this help menu
/save [filename]          - Save current world state
/load [filename]          - Load saved world state
/pause                    - Pause autonomous NPC activity
/resume                   - Resume autonomous NPC activity
/whisper NPC_NAME MESSAGE - Send a private message to an NPC
/npcs                     - List all NPCs in the world
/inspect NPC_NAME         - Inspect an NPC's details, memories, and relationships
/create NAME|PERS|BG      - Create a new NPC (e.g., /create Bob | Friendly | Carpenter)
/remove NPC_NAME          - Remove an NPC from the world"""

    def _save(self, filename: str = None) -> str:
        from pathlib import Path
        import config
        save_file = config.SAVE_DIR / filename if filename else config.DEFAULT_SAVE_FILE
        if SaveManager.save_world(self.world, save_file):
            return f"World saved successfully to {save_file.name}."
        return "Failed to save world state."

    def _load(self, filename: str = None) -> str:
        from pathlib import Path
        import config
        save_file = config.SAVE_DIR / filename if filename else config.DEFAULT_SAVE_FILE
        if SaveManager.load_world(self.world, save_file):
            return f"World loaded successfully from {save_file.name}."
        return f"Failed to load world state from {save_file.name}."

    def _list_npcs(self) -> str:
        if not self.world.npcs:
            return "No NPCs currently exist in the world."
        lines = ["NPCs in world:"]
        for name, npc in self.world.npcs.items():
            lines.append(f"- {name} ({npc.mood})")
        return "\n".join(lines)

    def _inspect_npc(self, name: str) -> str:
        npc = self.world.get_npc(name)
        if not npc:
            return f"NPC '{name}' not found."

        mems = npc.memory_store.get_all_facts()
        mem_str = "\n  ".join(mems) if mems else "None"
        rel_str = npc.get_relationship_summary()

        return f"""=== Inspect: {npc.name} ===
Personality: {npc.personality}
Background: {npc.background}
Interests: {', '.join(npc.interests)}
Dislikes: {', '.join(npc.dislikes)}
Mood: {npc.mood}

Memories:
  {mem_str}

Relationships:
  {rel_str}"""

    def _create_npc(self, args_str: str) -> str:
        parts = [p.strip() for p in args_str.split("|")]
        if len(parts) < 3:
            return "Usage: /create NAME | PERSONALITY | BACKGROUND"

        name, personality, background = parts[0], parts[1], parts[2]
        new_npc = NPC(name=name, personality=personality, background=background)
        if self.world.add_npc(new_npc):
            return f"Created NPC '{name}' successfully."
        return f"Failed to create NPC. An NPC with name '{name}' already exists."

    def _remove_npc(self, name: str) -> str:
        if self.world.remove_npc(name):
            return f"Removed NPC '{name}'."
        return f"NPC '{name}' not found."
