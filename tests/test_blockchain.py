import logging
import unittest

import os

from blockchain import Blockchain


class TestBlockchain(unittest.TestCase):
    valid_chain = 'tests/chain_data/valid_chain.txt'
    valid_message = 'tests/message_data/valid_public.txt'
    invalid_message = 'tests/message_data/bad_timestamp.txt'
    invalid_ds = 'tests/message_data/bad_ds.txt'
    ledger = 'tests/ledger.txt'
    example_ledger = 'tests/chain_data/ledger.txt'

    def setUp(self):
        try:
            os.remove(TestBlockchain.ledger)
        except OSError:
            pass
        logging.getLogger("blockchain").disabled = True

    def tearDown(self):
        try:
            os.remove(TestBlockchain.ledger)
        except OSError:
            pass

    def test_add_block_str(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.add_all_blocks(TestBlockchain.valid_chain)
        self.assertEqual(len(self.blockchain.get_all_block_strs(0)), 5)

    def test_message_queue_empty(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.assertEqual(self.blockchain.get_message_queue_size(), 0)

    def test_message_queue_single_message(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.blockchain.add_message_str(get_message_str(TestBlockchain.valid_message))
        self.assertEqual(1, self.blockchain.get_message_queue_size())

    def test_message_queue_no_duplicates(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        msg = get_message_str(TestBlockchain.valid_message)
        self.blockchain.add_message_str(msg)
        self.blockchain.add_message_str(msg)
        self.assertEqual(1, self.blockchain.get_message_queue_size())

    def test_message_queue_invalid_message(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.blockchain.add_message_str(get_message_str(TestBlockchain.invalid_message))
        self.assertEqual(self.blockchain.get_message_queue_size(), 0)

    def test_message_queue_wrong_ds(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.blockchain.add_message_str(get_message_str(TestBlockchain.invalid_ds))
        self.assertEqual(self.blockchain.get_message_queue_size(), 0)

    def test_no_mined_block(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.assertIsNone(self.blockchain.get_new_block_str())

    def test_no_saved_ledger(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.assertFalse(self.blockchain.get_all_block_strs(0))

    def test_saved_ledger(self):
        self.blockchain = Blockchain(TestBlockchain.example_ledger)
        self.assertEqual(11, len(self.blockchain.get_all_block_strs(0)))

    def test_get_all_block_strs(self):
        """
        Note that this test only works because our data only has a single chain of blocks. This means we are
        reading blocks in and printing the block string out in the same order.
        """
        self.blockchain = Blockchain(TestBlockchain.ledger)
        string = self.add_all_blocks(TestBlockchain.valid_chain)
        blocks = '\n'.join(self.blockchain.get_all_block_strs(0))
        self.assertEqual(string, blocks)

    def test_get_all_block_strs_time(self):
        self.blockchain = Blockchain(TestBlockchain.ledger)
        self.add_all_blocks(TestBlockchain.valid_chain)
        self.assertEqual(len(self.blockchain.get_all_block_strs(1519774044.163314)), 3)

    def add_all_blocks(self, file_name):
        with open(file_name, 'r') as chain:
            raw_data = chain.read().strip()
            blocks = raw_data.split("\n")
            for block_string in blocks:
                self.blockchain.add_block_str(block_string)
            return raw_data


def get_message_str(file):
    with open(file, 'r') as message:
        return message.read()


if __name__ == '__main__':
    unittest.main()
