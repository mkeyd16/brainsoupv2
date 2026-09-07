import random
import logging
import config
from world.world import World
from world.npc import NPC
from storage.save_manager import SaveManager

logger = logging.getLogger("wrld.world.commands")

RANDOM_NAMES = ["Karl", "Alex", "Clara", "David", "Elena", "Felix", "Gwen", "Hugo", "Iris", "Jesper", "Kira", "Leo", "Maya", "Nico", "Orla"]

class CommandHandler:
    def __init__(self, world: World):
        self.world = world
        self.pending_wipe = False

    def execute_command(self, raw_command: str) -> str:
        if self.pending_wipe:
            confirm_input = raw_command.strip().upper()
            if confirm_input in ["YES", "Y"]:
                self.pending_wipe = False
                return self._perform_wipe()
            else:
                self.pending_wipe = False
                return "Wipe canceled."

        if not raw_command.startswith("/"):
            return "Commands must start with '/'"

        parts = raw_command.strip().split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd in ["/help", "/cmds"]:
            return self._help_and_cmds()
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
        elif cmd == "/wipe":
            self.pending_wipe = True
            return "WARNING: /wipe will erase all current NPCs, memories, relationships, and save data.\nType 'YES' to confirm wipe or any other input to cancel."
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
        elif cmd == "/create":
            name_arg = parts[1] if len(parts) > 1 else None
            return self._create_npc(name_arg)
        elif cmd == "/remove":
            if len(parts) < 2:
                return "Usage: /remove NPC_NAME"
            return self._remove_npc(parts[1])
        else:
            return f"Unknown command '{cmd}'. Type /help or /cmds for available commands."

    def _help_and_cmds(self) -> str:
        return """Available Commands:
/help                     - Show this help menu
/cmds                     - Show this help menu (alias for /help)
/create [NAME]            - Create a new NPC (optional name, e.g. /create or /create Karl)
/remove NPC_NAME          - Remove an NPC from the simulation
/save [filename]          - Save current world state
/wipe                     - Clear all persistent simulation data (requires confirmation)
/whisper NPC_NAME MESSAGE - Send a private whisper to an NPC"""

    def _save(self, filename: str = None) -> str:
        import config
        save_file = config.SAVE_DIR / filename if filename else config.DEFAULT_SAVE_FILE
        if SaveManager.save_world(self.world, save_file):
            return f"World saved successfully to {save_file.name}."
        return "Failed to save world state."

    def _load(self, filename: str = None) -> str:
        import config
        save_file = config.SAVE_DIR / filename if filename else config.DEFAULT_SAVE_FILE
        if SaveManager.load_world(self.world, save_file):
            return f"World loaded successfully from {save_file.name}."
        return f"Failed to load world state from {save_file.name}."

    def _create_npc(self, name: str = None) -> str:
        if not name:
            existing_names = set(self.world.npcs.keys())
            available_names = [n for n in RANDOM_NAMES if n not in existing_names]
            if available_names:
                name = random.choice(available_names)
            else:
                name = f"Inhabitant_{len(self.world.npcs) + 1}"

        if name in self.world.npcs:
            return f"Failed to create NPC. An NPC with name '{name}' already exists."

        new_npc = NPC(
            name=name,
            personality="Curious, observant, adaptable.",
            background="Recently initialized into the simulation space.",
            interests=["exploring communication", "learning about ADMIN"],
            dislikes=["system errors"],
            mood="Neutral",
            temperament="Adaptive",
            existential_state="Newly aware of existence"
        )
        new_npc.add_memory("Initialized into the simulation.")

        if self.world.add_npc(new_npc, emit_event=True):
            return f"Created NPC '{name}' successfully."
        return f"Failed to create NPC '{name}'."

    def _remove_npc(self, name: str) -> str:
        if self.world.remove_npc(name):
            return f"Removed NPC '{name}'."
        return f"NPC '{name}' not found."

    def _perform_wipe(self) -> str:
        import config
        self.world.npcs.clear()
        self.world.conversation_manager.history.clear()

        if config.DEFAULT_SAVE_FILE.exists():
            try:
                config.DEFAULT_SAVE_FILE.unlink()
            except Exception as e:
                logger.error(f"Error removing save file during wipe: {e}")

        self.world.setup_starting_npcs_if_empty()
        return "Simulation wiped successfully. Initialized fresh world with 4 starting NPCs."
