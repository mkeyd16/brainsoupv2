import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import logging
from world.world import World
from world.commands import CommandHandler

logger = logging.getLogger("wrld.ui.gui")

class TkinterUI:
    def __init__(self, world: World):
        self.world = world
        self.cmd_handler = CommandHandler(world)
        # Root Window Setup
        self.root = tk.Tk()
        self.root.title("WRLD.V2 — Persistent AI Simulation")
        self.root.geometry("900x600")
        self.root.minsize(700, 450)

        self._configure_styles()
        self._build_layout()

        # Listen to simulation world events
        self.world.add_event_listener(self.on_world_event)

    def _configure_styles(self):
        self.bg_dark = "#1e1e24"
        self.bg_sidebar = "#2b2d42"
        self.bg_chat = "#18181c"
        self.text_color = "#edf2f4"
        self.accent_color = "#8d99ae"
        self.admin_color = "#4cc9f0"
        self.server_color = "#f72585"
        self.npc_color = "#7209b7"

        self.root.configure(bg=self.bg_dark)

    def _build_layout(self):
        # Main Paned Window
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 1. Left Sidebar - NPC List
        sidebar_frame = tk.Frame(paned, bg=self.bg_sidebar, width=200)
        paned.add(sidebar_frame, weight=1)

        sidebar_title = tk.Label(
            sidebar_frame,
            text="NPCs",
            font=("Helvetica", 14, "bold"),
            bg=self.bg_sidebar,
            fg=self.text_color,
            anchor="w",
            padx=10,
            pady=10
        )
        sidebar_title.pack(fill=tk.X)

        self.npc_listbox = tk.Listbox(
            sidebar_frame,
            bg=self.bg_sidebar,
            fg=self.text_color,
            selectbackground="#4a4e69",
            selectforeground="#ffffff",
            bd=0,
            font=("Helvetica", 11),
            highlightthickness=0
        )
        self.npc_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        hint_label = tk.Label(
            sidebar_frame,
            text="Active Simulation NPCs",
            font=("Helvetica", 9, "italic"),
            bg=self.bg_sidebar,
            fg=self.accent_color,
            pady=10
        )
        hint_label.pack(fill=tk.X)

        # 2. Central Chat & Input Area
        main_chat_frame = tk.Frame(paned, bg=self.bg_chat)
        paned.add(main_chat_frame, weight=4)

        # Scrollable Chat Log
        self.chat_display = scrolledtext.ScrolledText(
            main_chat_frame,
            bg=self.bg_chat,
            fg=self.text_color,
            font=("Consolas", 11),
            bd=0,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Configure Text Tags for Coloring
        self.chat_display.tag_config("ADMIN", foreground=self.admin_color, font=("Helvetica", 11, "bold"))
        self.chat_display.tag_config("SERVER", foreground=self.server_color, font=("Helvetica", 11, "bold"))
        self.chat_display.tag_config("NPC_NAME", foreground="#b5179e", font=("Helvetica", 11, "bold"))
        self.chat_display.tag_config("BODY", foreground=self.text_color, font=("Helvetica", 11))
        self.chat_display.tag_config("SYSTEM", foreground="#e0aaff", font=("Helvetica", 11, "italic"))

        # Bottom Input Bar
        input_frame = tk.Frame(main_chat_frame, bg=self.bg_chat)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.input_entry = tk.Entry(
            input_frame,
            bg="#2b2d42",
            fg=self.text_color,
            insertbackground=self.text_color,
            font=("Helvetica", 11),
            bd=1,
            relief=tk.FLAT
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=5)
        self.input_entry.bind("<Return>", lambda event: self.send_message())

        self.send_button = tk.Button(
            input_frame,
            text="Send",
            bg="#3a0ca3",
            fg="#ffffff",
            activebackground="#4361ee",
            activeforeground="#ffffff",
            font=("Helvetica", 10, "bold"),
            bd=0,
            padx=15,
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT)

        # Initial Refresh
        self.refresh_npc_list()

    def refresh_npc_list(self):
        self.npc_listbox.delete(0, tk.END)
        for name in sorted(self.world.npcs.keys()):
            npc = self.world.get_npc(name)
            mood = f" ({npc.mood})" if npc else ""
            self.npc_listbox.insert(tk.END, f"{name}{mood}")

    def append_message(self, sender: str, text: str, recipient: str = None):
        self.chat_display.config(state=tk.NORMAL)
        admin_name = getattr(config, "ADMIN_NAME", "MIKEY")

        if sender == "[SERVER]":
            self.chat_display.insert(tk.END, f"\n{text}\n", "SERVER")
        elif sender == admin_name or sender == "ADMIN":
            self.chat_display.insert(tk.END, f"\n{admin_name}\n", "ADMIN")
            self.chat_display.insert(tk.END, f"{text}\n", "BODY")
        else:
            self.chat_display.insert(tk.END, f"\n{sender.upper()}\n", "NPC_NAME")
            self.chat_display.insert(tk.END, f"{text}\n", "BODY")

        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def append_system_message(self, text: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n[SYSTEM]: {text}\n", "SYSTEM")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def on_world_event(self, event_type: str, data: dict):
        if event_type in ["npc_added", "npc_removed"]:
            self.root.after(0, self.refresh_npc_list)
        elif event_type == "message":
            sender = data.get("sender", "Unknown")
            text = data.get("text", "")
            recipient = data.get("recipient")
            self.root.after(0, self.append_message, sender, text, recipient)

    def send_message(self):
        user_input = self.input_entry.get().strip()
        if not user_input:
            return

        self.input_entry.delete(0, tk.END)

        if self.cmd_handler.pending_wipe:
            result = self.cmd_handler.execute_command(user_input)
            self.append_system_message(result)
            self.refresh_npc_list()
            return

        if user_input.startswith("/"):
            result = self.cmd_handler.execute_command(user_input)
            self.append_system_message(result)
            self.refresh_npc_list()
        else:
            # Send public ADMIN message in background to keep UI fluid
            threading.Thread(target=self.world.user_say_public, args=(user_input,), daemon=True).start()

    def start(self):
        # Ensure starting 4 NPCs on fresh launch
        self.world.setup_starting_npcs_if_empty()
        self.refresh_npc_list()

        # Display welcoming Banner
        self.append_system_message("wrld.v2 simulation window initialized. Talk publicly or use slash commands.")

        self.root.mainloop()
