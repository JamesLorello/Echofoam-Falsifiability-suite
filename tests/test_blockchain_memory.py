import os
import unittest
from blockchain_memory.blockchain_memory import BlockchainMemory

class BlockchainMemoryTest(unittest.TestCase):
    def setUp(self):
        self.path = "test_chain.json"
        if os.path.exists(self.path):
            os.remove(self.path)
        self.mem = BlockchainMemory(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_add_and_get_block(self):
        block = self.mem.add_memory("hello world")
        self.assertEqual(block.index, 0)
        self.assertTrue(block.hash)
        retrieved = self.mem.get_block(block.hash)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.hash, block.hash)

    def test_persistence(self):
        self.mem.add_memory("foo")
        self.mem.add_memory("bar")
        hashes_before = [b.hash for b in self.mem.chain]
        mem2 = BlockchainMemory(self.path)
        hashes_after = [b.hash for b in mem2.chain]
        self.assertEqual(hashes_before, hashes_after)

if __name__ == "__main__":
    unittest.main()
