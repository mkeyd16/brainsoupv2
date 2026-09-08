import unittest
import time
from world.npc import NPC
from world.conversation import ConversationManager
from world.scheduler import SimulationScheduler

class TestWorld(unittest.TestCase):
    def test_npc_creation_and_dict(self):
        npc = NPC(name="Finn", personality="Energetic", background="Explorer")
        npc.add_memory("Discovered a hidden pathway.")
        data = npc.to_dict()

        self.assertEqual(data["name"], "Finn")
        self.assertEqual(len(data["memories"]), 1)

        restored = NPC.from_dict(data)
        self.assertEqual(restored.name, "Finn")
        self.assertEqual(len(restored.memory_store.memories), 1)

    def test_whisper_privacy_routing(self):
        cm = ConversationManager()
        cm.add_message(sender="Finn", text="Public hello", is_whisper=False)
        cm.add_message(sender="Finn", text="Secret whisper to Sarah", recipient="Sarah", is_whisper=True)

        # Sarah sees the whisper
        sarah_view = cm.get_visible_history_for_participant("Sarah")
        self.assertEqual(len(sarah_view), 2)

        # Marcus should NOT see the whisper
        marcus_view = cm.get_visible_history_for_participant("Marcus")
        self.assertEqual(len(marcus_view), 1)
        self.assertEqual(marcus_view[0]["text"], "Public hello")

    def test_scheduler_cooldown(self):
        scheduler = SimulationScheduler(cooldown_seconds=0.1) # Fast deterministic 0.1s for test
        scheduler.start()

        results = []

        def mock_action(msg):
            return msg

        scheduler.set_message_callback(lambda res: results.append((time.time(), res)))

        t0 = time.time()
        scheduler.enqueue_action(lambda: mock_action("Msg 1"), npc_name="Finn")
        scheduler.enqueue_action(lambda: mock_action("Msg 2"), npc_name="Sarah")

        time.sleep(0.3)
        scheduler.stop()

        self.assertEqual(len(results), 2)
        time_diff = results[1][0] - results[0][0]
        self.assertGreaterEqual(time_diff, 0.08)

    def test_agent_self_message_exclusion_and_ai_to_ai_triggering(self):
        from world.world import World
        from ai.inference import InferenceEngine

        class EchoAI(InferenceEngine):
            def generate_npc_response(self, npc_name, personality, background, interests, dislikes, mood, temperament, existential_state, memories, relationships_summary, recent_chat_history, agent_id=None, max_retries=2, stream_callback=None):
                return f"Echo from {npc_name}"

        world = World(inference_engine=EchoAI())
        world.setup_starting_npcs_if_empty()

        # 1. Verify KARL's message does NOT trigger KARL
        candidates_for_karl_msg = [
            npc for name, npc in world.npcs.items()
            if npc.agent_id != "karl"
        ]
        self.assertNotIn("Karl", [c.name for c in candidates_for_karl_msg])
        self.assertIn("Sarah", [c.name for c in candidates_for_karl_msg])
        self.assertIn("Finn", [c.name for c in candidates_for_karl_msg])

        # 2. Verify ALICE's message does NOT trigger ALICE
        world.add_npc(NPC(name="Alice", personality="Smart", background="Coder"))
        candidates_for_alice_msg = [
            npc for name, npc in world.npcs.items()
            if npc.agent_id != "alice"
        ]
        self.assertNotIn("Alice", [c.name for c in candidates_for_alice_msg])
        self.assertIn("Karl", [c.name for c in candidates_for_alice_msg])

if __name__ == "__main__":
    unittest.main()
