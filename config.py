import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent.resolve()
MODELS_DIR = BASE_DIR / "models"
RUNTIME_DIR = BASE_DIR / "runtime"
DATA_DIR = BASE_DIR / "data"
SAVE_DIR = DATA_DIR / "saves"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
for directory in [MODELS_DIR, RUNTIME_DIR, DATA_DIR, SAVE_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Model Settings
MODEL_FILENAME = "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"
MODEL_PATH = MODELS_DIR / MODEL_FILENAME
MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
MIN_MODEL_SIZE_BYTES = 900 * 1024 * 1024

# Llama-cpp Runtime Settings (Optimized for <2.5GB RAM usage)
N_CTX = 2048
N_THREADS = max(1, min(4, (os.cpu_count() or 2) - 1))
N_BATCH = 512

# Simulation Settings
MESSAGE_COOLDOWN_SECONDS = 5.0  # Application-level minimum cooldown between NPC messages
AUTOSAVE_INTERVAL_SECONDS = 60.0
AUTONOMOUS_TICK_INTERVAL_SECONDS = 2.0  # How often scheduler checks for NPC actions

# Memory and Context Limits
MAX_PROMPT_MEMORIES = 5
MAX_PROMPT_HISTORY = 8
MAX_RESPONSE_SENTENCES = 5
DEFAULT_MAX_TOKENS = 128
TEMPERATURE = 0.7
TOP_P = 0.9

# Persistence
DEFAULT_SAVE_FILE = SAVE_DIR / "default_world.json"
LOG_FILE = LOGS_DIR / "wrld.log"
