import unittest
import tempfile
from pathlib import Path
from world.world import World
from world.commands import CommandHandler
from storage.save_manager import SaveManager

class TestStorageAndCommands(unittest.TestCase):
    def setUp(self):
        self.world = World()
        self.cmd = CommandHandler(self.world)

    def test_save_load_world(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_file = Path(tmpdir) / "test_save.json"
            self.world.user_say_public("Hello wrld!")

            # Save
            res = SaveManager.save_world(self.world, save_file)
            self.assertTrue(res)
            self.assertTrue(save_file.exists())

            # Load into new world instance
            new_world = World()
            load_res = SaveManager.load_world(new_world, save_file)
            self.assertTrue(load_res)
            self.assertIn("Finn", new_world.npcs)
            self.assertEqual(len(new_world.conversation_manager.history), 1)

    def test_commands(self):
        # /help
        help_out = self.cmd.execute_command("/help")
        self.assertIn("Available Commands", help_out)

        # /npcs
        npcs_out = self.cmd.execute_command("/npcs")
        self.assertIn("Finn", npcs_out)

        # /create
        create_out = self.cmd.execute_command("/create Clara | Gentle | Florist")
        self.assertIn("Clara", create_out)
        self.assertIn("Clara", self.world.npcs)

        # /inspect
        inspect_out = self.cmd.execute_command("/inspect Clara")
        self.assertIn("Florist", inspect_out)

        # /remove
        remove_out = self.cmd.execute_command("/remove Clara")
        self.assertNotIn("Clara", self.world.npcs)

        # /pause and /resume
        pause_out = self.cmd.execute_command("/pause")
        self.assertTrue(self.world.scheduler.is_paused)
        resume_out = self.cmd.execute_command("/resume")
        self.assertFalse(self.world.scheduler.is_paused)

if __name__ == "__main__":
    unittest.main()
