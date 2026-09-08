import time
import queue
import threading
import logging
import config

logger = logging.getLogger("wrld.world.scheduler")

class SimulationScheduler:
    def __init__(self, cooldown_seconds: float = config.MESSAGE_COOLDOWN_SECONDS):
        self.cooldown_seconds = cooldown_seconds
        self.last_message_time = 0.0
        self.action_queue = queue.Queue()
        self.is_paused = False
        self.is_running = False
        self._lock = threading.Lock()
        self._worker_thread = None
        self.message_callback = None

    def set_message_callback(self, callback):
        self.message_callback = callback

    def enqueue_action(self, action_func, npc_name: str, is_direct_user_request: bool = False, *args, **kwargs):
        self.action_queue.put((action_func, npc_name, is_direct_user_request, args, kwargs))

    def pause(self):
        with self._lock:
            self.is_paused = True
            logger.info("Scheduler paused.")

    def resume(self):
        with self._lock:
            self.is_paused = False
            logger.info("Scheduler resumed.")

    def start(self):
        with self._lock:
            if self.is_running:
                return
            self.is_running = True
            self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._worker_thread.start()
            logger.info("Scheduler thread started.")

    def stop(self):
        with self._lock:
            self.is_running = False

    def _run_loop(self):
        while self.is_running:
            if self.is_paused:
                time.sleep(0.05)
                continue

            try:
                action_tuple = self.action_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            action_func, npc_name, is_direct_user_request, args, kwargs = action_tuple

            now = time.time()
            elapsed = now - self.last_message_time
            # Direct user requests bypass background idle cooldowns to minimize response latency
            if not is_direct_user_request and elapsed < self.cooldown_seconds:
                wait_time = self.cooldown_seconds - elapsed
                time.sleep(wait_time)

            try:
                result = action_func(*args, **kwargs)
                self.last_message_time = time.time()
                if result and self.message_callback:
                    self.message_callback(result)
            except Exception as e:
                logger.error(f"Error executing enqueued action for NPC '{npc_name}': {e}")
            finally:
                self.action_queue.task_done()
