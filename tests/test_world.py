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

    def test_unknown_whisper_command(self):
        from world.world import World
        from world.commands import CommandHandler

        world = World()
        cmd = CommandHandler(world)
        res = cmd.execute_command("/whisper Sarah hello")
        self.assertIn("Unknown command", res)

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

    def test_direct_question_priority_and_turn_taking(self):
        from world.world import World
        from ai.inference import InferenceEngine
        import config

        class EchoAI(InferenceEngine):
            def generate_npc_response(self, npc_name, personality, background, interests, dislikes, mood, temperament, existential_state, memories, relationships_summary, recent_chat_history, agent_id=None, max_retries=2, stream_callback=None):
                return f"Echo from {npc_name}"

        world = World(inference_engine=EchoAI())
        world.setup_starting_npcs_if_empty()
        world.add_npc(NPC(name="Alice", personality="Smart", background="Coder"))
        world.add_npc(NPC(name="Bob", personality="Calm", background="Builder"))

        # Test A: Direct Question (KARL asks ALICE -> ALICE selected)
        enqueued = []
        world._enqueue_npc_speech = lambda npc, **kw: enqueued.append(npc.name)
        world.trigger_npc_responses("Alice, what do you think about the plan?", sender_name="Karl", sender_id="karl", is_user=False)
        self.assertEqual(enqueued, ["Alice"])

        # Test B: Self-trigger prevention (KARL -> KARL 100% blocked)
        enqueued.clear()
        world.trigger_npc_responses("General statement about weather.", sender_name="Karl", sender_id="karl", is_user=False, probability=1.0)
        self.assertNotIn("Karl", enqueued)
        self.assertGreater(len(enqueued), 0)

        # Test C: Turn taking preference (After ALICE speaks, KARL becomes eligible again)
        enqueued.clear()
        world.conversation_manager.last_speaker_id = "alice"
        world.trigger_npc_responses("I agree with Alice.", sender_name="Alice", sender_id="alice", is_user=False, probability=1.0)
        self.assertNotIn("Alice", enqueued)
        self.assertTrue(any(name in ["Karl", "Finn", "Sarah", "Alex", "Bob"] for name in enqueued))

        # Test F: Cooldown configuration verification
        self.assertEqual(config.MESSAGE_COOLDOWN_SECONDS, 3.0)

if __name__ == "__main__":
    unittest.main()
