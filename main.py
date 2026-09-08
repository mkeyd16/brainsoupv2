import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

import time
import logging
import threading
import config
from launch import verify_and_setup_environment
from ai.model import ModelManager
from world.world import World
from storage.save_manager import SaveManager
from ui.gui import TkinterUI

logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("wrld.main")

def start_autonomous_loop(world: World, stop_event: threading.Event):
    while not stop_event.is_set():
        time.sleep(config.AUTONOMOUS_TICK_INTERVAL_SECONDS)
        try:
            world.autonomous_tick()
        except Exception as e:
            logger.error(f"Error during autonomous tick: {e}")

def start_autosave_loop(world: World, stop_event: threading.Event):
    while not stop_event.is_set():
        time.sleep(config.AUTOSAVE_INTERVAL_SECONDS)
        try:
            SaveManager.save_world(world, config.DEFAULT_SAVE_FILE)
            logger.info("Auto-saved world state.")
        except Exception as e:
            logger.error(f"Error during auto-save: {e}")

def main():
    print("Initializing wrld.v2 persistent society...\n")

    if not verify_and_setup_environment():
        print("ERROR: Environment setup failed. Cannot start wrld.v2.")
        sys.exit(1)

    model_mgr = ModelManager.get_instance()
    if not model_mgr.load_model(str(config.MODEL_PATH)):
        print("Failed to initialize LLM engine. Please check logs.")
        sys.exit(1)

    world = World()
    if config.DEFAULT_SAVE_FILE.exists():
        print(f"Loading persistent world state from {config.DEFAULT_SAVE_FILE.name}...")
        SaveManager.load_world(world, config.DEFAULT_SAVE_FILE)

    world.scheduler.start()

    stop_threads = threading.Event()
    auto_thread = threading.Thread(target=start_autonomous_loop, args=(world, stop_threads), daemon=True)
    autosave_thread = threading.Thread(target=start_autosave_loop, args=(world, stop_threads), daemon=True)

    auto_thread.start()
    autosave_thread.start()

    ui = TkinterUI(world)
    try:
        ui.start()
    finally:
        print("Shutting down wrld.v2 simulation...")
        stop_threads.set()
        world.scheduler.stop()
        SaveManager.save_world(world, config.DEFAULT_SAVE_FILE)
        print("World saved. Goodbye!")

if __name__ == "__main__":
    main()
