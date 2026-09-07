import sys
import os
import threading
import time
from world.world import World
from world.commands import CommandHandler

class TerminalUI:
    def __init__(self, world: World):
        self.world = world
        self.cmd_handler = CommandHandler(world)
        self.is_running = True
        self.world.add_event_listener(self.on_world_event)

    def on_world_event(self, event_type: str, data: dict):
        if event_type == "message":
            sender = data.get("sender", "Unknown")
            text = data.get("text", "")
            is_whisper = data.get("is_whisper", False)
            recipient = data.get("recipient")

            if is_whisper:
                print(f"\n[WHISPER {sender} -> {recipient}]: {text}")
            else:
                print(f"\n[{sender}]: {text}")
            print("> ", end="", flush=True)

    def start(self):
        print("==================================================")
        print("              WRLD.V2 AI SIMULATION               ")
        print("==================================================")
        print("Type your message to talk publicly.")
        print("Type commands starting with '/' (e.g. /help, /whisper NPC message).")
        print("Type /exit or /quit to exit application.")
        print("--------------------------------------------------\n")

        print("> ", end="", flush=True)

        while self.is_running:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                user_input = line.strip()
                if not user_input:
                    print("> ", end="", flush=True)
                    continue

                if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                    print("\nExiting wrld.v2...")
                    self.is_running = False
                    break

                if user_input.startswith("/"):
                    result = self.cmd_handler.execute_command(user_input)
                    print(f"\n[SYSTEM]: {result}")
                    print("> ", end="", flush=True)
                else:
                    self.world.user_say_public(user_input)

            except KeyboardInterrupt:
                print("\nExiting wrld.v2...")
                self.is_running = False
                break
            except Exception as e:
                print(f"\n[ERROR]: {e}")
                print("> ", end="", flush=True)
