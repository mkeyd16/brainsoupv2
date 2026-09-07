import unittest
import time
from world.world import World
from world.npc import NPC
from world.commands import CommandHandler
from storage.save_manager import SaveManager
from ai.inference import InferenceEngine

class MockInferenceEngine(InferenceEngine):
    def generate_npc_response(self, npc_name, personality, background, interests, dislikes, mood, temperament, existential_state, memories, relationships_summary, recent_chat_history, max_retries=2):
        return f"I am {npc_name} and I hear you loud and clear!"

class TestIntegrationSimulation(unittest.TestCase):
    def test_full_simulation_flow(self):
        mock_ai = MockInferenceEngine()
        world = World(inference_engine=mock_ai)
        world.setup_starting_npcs_if_empty()
        world.scheduler.cooldown_seconds = 0.05
        world.scheduler.start()

        cmd = CommandHandler(world)

        try:
            received_messages = []
            world.add_event_listener(lambda etype, data: received_messages.append((etype, data)) if etype == "message" else None)

            world.user_say_public("Hello Finn, how are you?")
            time.sleep(0.3)

            self.assertGreater(len(received_messages), 1)

            world.user_whisper("Finn", "Secret meeting at noon.")
            time.sleep(0.3)

            finn_vis = world.conversation_manager.get_visible_history_for_participant("Finn")
            sarah_vis = world.conversation_manager.get_visible_history_for_participant("Sarah")

            self.assertTrue(any("Secret meeting" in m["text"] for m in finn_vis))
            self.assertFalse(any("Secret meeting" in m["text"] for m in sarah_vis))

            create_res = cmd.execute_command("/create Hugo")
            self.assertIn("Hugo", create_res)

            hugo = world.get_npc("Hugo")
            hugo.add_memory("Baked fresh sourdough bread.")

            save_res = cmd.execute_command("/save integration_world.json")
            self.assertIn("successfully", save_res)

            new_world = World(inference_engine=mock_ai)
            load_res = CommandHandler(new_world).execute_command("/load integration_world.json")
            self.assertIn("successfully", load_res)

            self.assertIn("Hugo", new_world.npcs)
            self.assertEqual(new_world.get_npc("Hugo").get_relevant_memories()[0], "Baked fresh sourdough bread.")

        finally:
            world.scheduler.stop()

if __name__ == "__main__":
    unittest.main()
