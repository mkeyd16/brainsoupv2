import json
import os
import logging
from pathlib import Path
import config
from world.world import World
from world.npc import NPC

logger = logging.getLogger("wrld.storage.save_manager")

class SaveManager:
    @staticmethod
    def save_world(world: World, filepath: Path = config.DEFAULT_SAVE_FILE) -> bool:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp_filepath = filepath.with_suffix(".tmp")

        state = {
            "version": "2.0",
            "npcs": {name: npc.to_dict() for name, npc in world.npcs.items()},
            "conversation_history": world.conversation_manager.to_list(),
            "user_name": world.user_name
        }

        try:
            with open(tmp_filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            os.replace(tmp_filepath, filepath)
            logger.info(f"World state successfully saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save world state: {e}")
            if os.path.exists(tmp_filepath):
                try:
                    os.remove(tmp_filepath)
                except Exception:
                    pass
            return False

    @staticmethod
    def load_world(world: World, filepath: Path = config.DEFAULT_SAVE_FILE) -> bool:
        filepath = Path(filepath)
        if not filepath.exists():
            logger.warning(f"Save file not found at {filepath}")
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            world.npcs.clear()
            for name, npc_data in state.get("npcs", {}).items():
                npc = NPC.from_dict(npc_data)
                world.npcs[name] = npc

            if "conversation_history" in state:
                world.conversation_manager.load_from_list(state["conversation_history"])

            if "user_name" in state:
                world.user_name = state["user_name"]

            logger.info(f"World state successfully loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load save file {filepath}: {e}")
            return False
