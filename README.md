# wrld.v2 — Persistent AI Society

**wrld.v2** is a local, persistent artificial society populated by autonomous AI-controlled NPCs running entirely on your local computer.

---

## Key Features

- **Local Inference Engine**: Powered by **Qwen2.5-1.5B-Instruct** (`Q4_K_M GGUF`) using `llama-cpp-python`.
- **Single Shared LLM Instance**: One loaded model handles dialogue for all NPCs, minimizing RAM usage to fit comfortably under **2.5 GB total RAM**.
- **Speech-Only AI Output**: Post-processing sanitizer guarantees NPCs only output spoken words—never stage directions, `<think>` blocks, or internal metadata.
- **Autonomous NPC Society**: NPCs initiate conversations, respond to world events, and interact based on individual personalities, moods, memories, and relationships.
- **Shared Autonomous World**: Public conversations where NPCs communicate with MIKEY and each other naturally.
- **Enforced Cooldown**: Global 3.0-second minimum message cooldown managed by a central application-level scheduler.
- **Persistent State**: Save and load world state, NPC memories, and relationships atomically.
- **One-Click Startup**: Windows `startup.bat` automatically checks, downloads, verifies, and launches everything.

---

## Hardware & Environment Requirements

- **Operating System**: Windows 10/11, Linux, or macOS.
- **Python**: Python 3.10+ installed and available in PATH.
- **RAM Expectation**: Designed for low-end machines. Absolute target is **< 2.5 GB RAM**.
- **Disk Space**: ~1.2 GB free space (for the GGUF model and dependencies).
- **Internet Connection**: Required ONLY on initial launch to download model/dependencies. Operates 100% offline afterwards.

---

## One-Click Launch

Double-click `startup.bat` on Windows (or run `python launch.py && python main.py` on Linux/macOS).

On first startup, wrld.v2 will automatically:
1. Verify Python installation.
2. Install missing dependencies from `requirements.txt`.
3. Safely download `Qwen2.5-1.5B-Instruct-Q4_K_M.gguf` into a `.part` temporary file and verify its size/integrity.
4. Launch the simulation.

Subsequent launches verify components instantly and launch without downloading.

---

## Available Commands

In the interactive prompt, type `/` followed by a command:

| Command | Description |
|---|---|
| `/help` | Display the command help menu |
| `/save [filename]` | Save current world state (default: `default_world.json`) |
| `/load [filename]` | Load saved world state |
| `/pause` | Pause autonomous NPC activity |
| `/resume` | Resume autonomous NPC activity |
| `/create NAME \| ROLE \| BG` | Create a new NPC with generated persona (e.g. `/create Clara \| Florist \| Loves plants`) |
| `/remove NPC_NAME` | Remove an NPC from the world |
| `/wipe` | Completely reset simulation state and clear all save files |

---

## Project Architecture

```text
wrld.v2/
├── startup.bat               # Windows launcher script
├── launch.py                 # Auto-detection, package installer & safe GGUF downloader
├── main.py                   # Entry point initializing LLM, world, threads & UI
├── config.py                 # Central configuration (RAM settings, cooldown, URLs)
├── requirements.txt          # Minimal Python dependencies
├── README.md                 # Documentation
├── ai/                       # LLM Inference & Sanitization
│   ├── model.py              # Singleton Llama model manager
│   ├── inference.py          # LLM execution interface
│   ├── sanitizer.py          # Dialogue sanitization & clean speech filter
│   └── prompts.py            # Compact prompt templates
├── world/                    # Simulation Logic & Scheduling
│   ├── world.py              # World engine managing simulation logic
│   ├── npc.py                # NPC identity, personality & state
│   ├── conversation.py       # Message router & history manager
│   ├── scheduler.py          # Central turn scheduler enforcing 3.0s cooldown
│   ├── relationships.py      # NPC-to-NPC relationship manager
│   └── commands.py           # Command handler (/save, /load, /create, /wipe, etc.)
├── memory/                   # Memory System
│   ├── memory_store.py       # NPC fact memory storage with internal tag filters
│   └── memory_retrieval.py   # Compact top-K memory retriever
├── storage/                  # State Persistence
│   └── save_manager.py       # Atomic JSON save/load manager
├── ui/                       # User Interface
│   └── cli.py                # Terminal UI
└── tests/                    # Automated Test Suite
    ├── test_ai.py
    ├── test_memory_rel.py
    ├── test_world.py
    ├── test_storage_cmd.py
    ├── test_launch.py
    └── test_integration.py
```

---

## Running Automated Tests

To run the complete automated test suite:

```bash
python -m unittest
```

All 18 unit and integration tests run deterministically using mock inference and complete in under 1 second.
