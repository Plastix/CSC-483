import logging
import unittest

from blockchain import Blockchain


class TestBlockchain(unittest.TestCase):
    valid_chain = 'tests/chain_data/valid_chain.txt'

    def setUp(self):
        logging.getLogger("blockchain").disabled = True
        self.blockchain = Blockchain()

    def test_add_block_str(self):
        self.add_all_blocks(TestBlockchain.valid_chain)
        self.assertEqual(len(self.blockchain.get_all_block_strs(0)), 5)

    def test_get_all_block_strs(self):
        """
        Note that this test only works because our data only has a single chain of blocks. This means we are
        reading blocks in and printing the block string out in the same order.
        """
        string = self.add_all_blocks(TestBlockchain.valid_chain)
        blocks = '\n'.join(self.blockchain.get_all_block_strs(0))
        self.assertEqual(string, blocks)

    def test_get_all_block_strs_time(self):
        self.add_all_blocks(TestBlockchain.valid_chain)
        self.assertEqual(len(self.blockchain.get_all_block_strs(1519774044.163314)), 3)

    def add_all_blocks(self, file_name):
        with open(file_name, 'r') as chain:
            raw_data = chain.read().strip()
            blocks = raw_data.split("\n")
            for block_string in blocks:
                self.blockchain.add_block_str(block_string)
            return raw_data


if __name__ == '__main__':
    unittest.main()
