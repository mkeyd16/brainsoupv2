import unittest
import time
import tempfile
from pathlib import Path
from world.world import World
from world.npc import NPC
from world.commands import CommandHandler
from storage.save_manager import SaveManager
from ai.inference import InferenceEngine

class MockInferenceEngine(InferenceEngine):
    def generate_npc_response(self, npc_name, personality, background, interests, dislikes, mood, temperament, existential_state, memories, relationships_summary, recent_chat_history, max_retries=2):
        return f"Sarah: I am actually Sarah pretending to be {npc_name}!" if npc_name == "Finn" else f"I am {npc_name} in this text simulation."

class TestWrldV2Requirements(unittest.TestCase):

    def setUp(self):
        self.mock_ai = MockInferenceEngine()
        self.world = World(inference_engine=self.mock_ai)
        self.world.setup_starting_npcs_if_empty()
        self.world.scheduler.cooldown_seconds = 0.05
        self.cmd = CommandHandler(self.world)

    def test_starting_npcs_count_and_uniqueness(self):
        self.assertEqual(len(self.world.npcs), 4)
        names = set(self.world.npcs.keys())
        self.assertEqual(names, {"Finn", "Sarah", "Karl", "Alex"})

        self.world.setup_starting_npcs_if_empty()
        self.assertEqual(len(self.world.npcs), 4)

    def test_speaker_identity_enforcement(self):
        # Speaker attribution check: when Finn generates speech, sender MUST be Finn
        finn = self.world.get_npc("Finn")
        memories = finn.get_relevant_memories("test")
        rel_summary = finn.get_relationship_summary()
        chat_history = self.world.conversation_manager.get_visible_history_for_participant("Finn")

        reply_text = self.mock_ai.generate_npc_response(
            npc_name=finn.name,
            personality=finn.personality,
            background=finn.background,
            interests=finn.interests,
            dislikes=finn.dislikes,
            mood=finn.mood,
            temperament=finn.temperament,
            existential_state=finn.existential_state,
            memories=memories,
            relationships_summary=rel_summary,
            recent_chat_history=chat_history
        )

        from ai.sanitizer import sanitize_dialogue
        cleaned_text = sanitize_dialogue(reply_text, npc_name=finn.name)

        # Application assigns sender identity
        msg_dict = {
            "sender": finn.name,
            "text": cleaned_text,
            "recipient": None,
            "is_whisper": False
        }

        self.assertEqual(msg_dict["sender"], "Finn")
        self.assertEqual(cleaned_text, "I am actually Sarah pretending to be Finn!")

    def test_admin_identity(self):
        import config
        received_messages = []
        self.world.add_event_listener(lambda etype, data: received_messages.append(data) if etype == "message" else None)

        self.world.user_say_public("Hello world")
        self.assertEqual(received_messages[0]["sender"], config.ADMIN_NAME)

    def test_cmds_alias_of_help(self):
        help_out = self.cmd.execute_command("/help")
        cmds_out = self.cmd.execute_command("/cmds")
        self.assertEqual(help_out, cmds_out)
        self.assertIn("/help", cmds_out)
        self.assertIn("/cmds", cmds_out)

    def test_command_invisibility_and_server_events(self):
        received_messages = []
        self.world.add_event_listener(lambda etype, data: received_messages.append(data) if etype == "message" else None)

        res_create = self.cmd.execute_command("/create Hugo")
        self.assertIn("Hugo", res_create)

        hist = self.world.conversation_manager.history
        self.assertFalse(any("/create" in m.text for m in hist))

        server_msgs = [m.text for m in hist if m.sender == "[SERVER]"]
        self.assertTrue(any("Hugo has joined the simulation." in m for m in server_msgs))

        res_remove = self.cmd.execute_command("/remove Hugo")
        self.assertIn("Removed", res_remove)
        self.assertFalse(any("/remove" in m.text for m in hist))
        server_msgs = [m.text for m in hist if m.sender == "[SERVER]"]
        self.assertTrue(any("Hugo has been removed from the simulation." in m for m in server_msgs))

    def test_wipe_confirmation_flow(self):
        res1 = self.cmd.execute_command("/wipe")
        self.assertIn("WARNING", res1)
        self.assertTrue(self.cmd.pending_wipe)

        res2 = self.cmd.execute_command("NO")
        self.assertIn("canceled", res2)
        self.assertFalse(self.cmd.pending_wipe)
        self.assertEqual(len(self.world.npcs), 4)

        self.cmd.execute_command("/wipe")
        res3 = self.cmd.execute_command("YES")
        self.assertIn("wiped successfully", res3)
        self.assertEqual(len(self.world.npcs), 4)

    def test_cooldown_enforcement(self):
        from world.scheduler import SimulationScheduler
        sched = SimulationScheduler(cooldown_seconds=0.2)
        sched.start()
        res_times = []

        sched.set_message_callback(lambda res: res_times.append(time.time()))

        sched.enqueue_action(lambda: "Msg 1", npc_name="Finn")
        sched.enqueue_action(lambda: "Msg 2", npc_name="Sarah")

        time.sleep(0.5)
        sched.stop()

        self.assertEqual(len(res_times), 2)
        diff = res_times[1] - res_times[0]
        self.assertGreaterEqual(diff, 0.18)

if __name__ == "__main__":
    unittest.main()
