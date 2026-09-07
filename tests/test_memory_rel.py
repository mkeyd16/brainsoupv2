import unittest
from memory.memory_store import MemoryStore
from memory.memory_retrieval import retrieve_relevant_memories
from world.relationships import Relationships, RelationshipTier

class TestMemoryAndRelationships(unittest.TestCase):
    def test_memory_store_filtering(self):
        store = MemoryStore()
        # Valid memory
        self.assertTrue(store.add_memory("Alex loves playing Minecraft."))
        # Invalid memory with forbidden keyword
        self.assertFalse(store.add_memory("USER INTENT: user wants to check Minecraft."))
        self.assertFalse(store.add_memory("Contains <think> tag inside"))

        facts = store.get_all_facts()
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0], "Alex loves playing Minecraft.")

    def test_memory_retrieval(self):
        store = MemoryStore()
        store.add_memory("Marcus likes eating spicy ramen.")
        store.add_memory("Sarah went to the library yesterday.")
        store.add_memory("Alex bought a new keyboard.")

        retrieved = retrieve_relevant_memories(store, query_text="Does anyone like ramen or food?")
        self.assertTrue(len(retrieved) > 0)
        self.assertEqual(retrieved[0], "Marcus likes eating spicy ramen.")

    def test_relationships(self):
        rel = Relationships()
        self.assertEqual(rel.get_relationship("Sarah")["tier"], RelationshipTier.STRANGER)

        rel.modify_score("Sarah", 30)
        self.assertEqual(rel.get_relationship("Sarah")["tier"], RelationshipTier.ACQUAINTANCE)

        rel.modify_score("Sarah", 35)
        self.assertEqual(rel.get_relationship("Sarah")["tier"], RelationshipTier.FRIEND)

        rel.modify_score("Jake", -40)
        self.assertEqual(rel.get_relationship("Jake")["tier"], RelationshipTier.RIVAL)

if __name__ == "__main__":
    unittest.main()
