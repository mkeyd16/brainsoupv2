import unittest
import time
from world.world import World
from world.npc import NPC
from world.commands import CommandHandler
from storage.save_manager import SaveManager
from ai.inference import InferenceEngine

class MockInferenceEngine(InferenceEngine):
    def generate_npc_response(self, npc_name, personality, background, interests, dislikes, mood, memories, relationships_summary, recent_chat_history, max_retries=2):
        return f"I am {npc_name} and I hear you loud and clear!"

class TestIntegrationSimulation(unittest.TestCase):
    def test_full_simulation_flow(self):
        # 1. Initialize World with Mock Inference
        mock_ai = MockInferenceEngine()
        world = World(inference_engine=mock_ai)
        world.scheduler.cooldown_seconds = 0.1 # Fast cooldown for integration test
        world.scheduler.start()

        cmd = CommandHandler(world)

        try:
            # 2. Public conversation
            received_messages = []
            world.add_event_listener(lambda etype, data: received_messages.append((etype, data)) if etype == "message" else None)

            world.user_say_public("Hello everyone in town!")
            time.sleep(0.3) # Allow scheduler to process NPC responses

            self.assertGreater(len(received_messages), 1)

            # 3. Whisper privacy
            world.user_whisper("Finn", "Secret meeting at noon.")
            time.sleep(0.3)

            finn_vis = world.conversation_manager.get_visible_history_for_participant("Finn")
            sarah_vis = world.conversation_manager.get_visible_history_for_participant("Sarah")

            # Finn should see the whisper, Sarah should not
            self.assertTrue(any("Secret meeting" in m["text"] for m in finn_vis))
            self.assertFalse(any("Secret meeting" in m["text"] for m in sarah_vis))

            # 4. Command execution
            create_res = cmd.execute_command("/create Clara | Cheerful | Baker")
            self.assertIn("Clara", create_res)

            # 5. Memory & Relationships persistence
            clara = world.get_npc("Clara")
            clara.add_memory("Baked fresh sourdough bread.")

            save_res = cmd.execute_command("/save integration_world.json")
            self.assertIn("successfully", save_res)

            # Load into fresh world
            new_world = World(inference_engine=mock_ai)
            load_res = CommandHandler(new_world).execute_command("/load integration_world.json")
            self.assertIn("successfully", load_res)

            self.assertIn("Clara", new_world.npcs)
            self.assertEqual(new_world.get_npc("Clara").get_relevant_memories()[0], "Baked fresh sourdough bread.")

        finally:
            world.scheduler.stop()

if __name__ == "__main__":
    unittest.main()
