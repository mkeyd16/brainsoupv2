import unittest
from ai.sanitizer import sanitize_dialogue
from ai.prompts import build_npc_system_prompt, format_chat_history

class TestAI(unittest.TestCase):
    def test_sanitize_dialogue_clean(self):
        raw = 'Finn looks at Marcus and smiles. "Hey, what\'s up?"'
        cleaned = sanitize_dialogue(raw, npc_name="Finn")
        self.assertEqual(cleaned, "Hey, what's up?")

    def test_sanitize_dialogue_think_block(self):
        raw = '<think>I should greet the user warmly.</think> Finn: Hello there! Nice to meet you.'
        cleaned = sanitize_dialogue(raw, npc_name="Finn")
        self.assertEqual(cleaned, "Hello there! Nice to meet you.")

    def test_sanitize_dialogue_meta_tags(self):
        raw = 'USER INTENT: Greeting.\nFinn says: Good morning!'
        cleaned = sanitize_dialogue(raw, npc_name="Finn")
        self.assertEqual(cleaned, "Good morning!")

    def test_prompt_formatting(self):
        prompt = build_npc_system_prompt(
            npc_name="Alex",
            personality="Friendly",
            background="Local baker",
            interests=["baking", "crafting"],
            dislikes=["rain"],
            mood="happy",
            temperament="Sanguine",
            existential_state="Reflective",
            memories=["Met Sarah yesterday."],
            relationships_summary="Sarah: Friend"
        )
        self.assertIn("Alex", prompt)
        self.assertIn("INTERACTION CONTEXT & IDENTITY GUIDELINES", prompt)
        self.assertIn("Met Sarah yesterday.", prompt)

if __name__ == "__main__":
    unittest.main()
