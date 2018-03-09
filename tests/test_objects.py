import hashlib
import logging
import unittest

from blockchain_constants import MSGS_PER_BLOCK
from key import Keys
from objects import parse_block, parse_message

private = "tests/key_data/private_keys.pem"
public = "tests/key_data/public_keys.pem"
directory = "tests/key_data/key_directory.pem"


class TestBlockParsing(unittest.TestCase):
    block_data_path = 'tests/block_data/'
    block_tests = [
        ["parse_valid_block", "valid_block.txt", True],
        ["parse_random", "random.txt", False],
        ["parse_empty", "empty.txt", False],
        ["parse_empty_nonce", "empty_nonce.txt", False],
        ["parse_bad_nonce", "bad_nonce.txt", False],
        ["parse_empty_parent_hash", "empty_parent_hash.txt", False],
        ["parse_bad_parent_hash", "bad_parent_hash.txt", False],
        ["parse_no_messages", "no_messages.txt", False],
        ["parse_empty_messages", "empty_messages.txt", False],
        ["parse_empty_miner_id", "empty_miner_id.txt", False],
        ["parse_bad_miner_id", "bad_miner_id.txt", False],
        ["parse_empty_timestamp", "empty_timestamp.txt", False],
        ["parse_bad_timestamp", "bad_timestamp.txt", False],
    ]

    @staticmethod
    def generate_block_test(file, result):
        def test(self):
            with open(TestBlockParsing.block_data_path + file, 'r') as data:
                string = data.read()
                block = parse_block(string)
                if result:
                    self.assertTrue(block)
                else:
                    self.assertFalse(block)

        return test

    @staticmethod
    def setup_tests():
        for test in TestBlockParsing.block_tests:
            test_name = 'test_%s' % test[0]
            func = TestBlockParsing.generate_block_test(test[1], test[2])
            setattr(TestBlockParsing, test_name, func)

    def test_to_string(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            string = data.read()
            self.assertEqual(repr(parse_block(string)), string)

    def test_parsing_data(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            block = parse_block(data.read())
            self.assertEqual(block.nonce, 280815619281315998298257152433917011173307790385)
            self.assertEqual(block.parent_hash, "000000000000000000000000000000000000")
            self.assertEqual(block.create_time, 1519773893.9249759)
            self.assertEqual(block.miner_key_hash, "03586f81a493d12fc4c71a01d648f83ac5d544e7168f96dcc32fa6bd4d54992e")
            self.assertEqual(len(block.posts), MSGS_PER_BLOCK)

    def test_correct_pow(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            block = parse_block(data.read())
            self.assertTrue(block.verify_pow())

    def test_wrong_pow(self):
        with open(TestBlockParsing.block_data_path + 'invalid_nonce.txt', 'r') as data:
            block = parse_block(data.read())
            self.assertFalse(block.verify_pow())

    def test_parent_block(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            block = parse_block(data.read())
            self.assertTrue(block.is_root())

    def test_not_parent_block(self):
        with open(TestBlockParsing.block_data_path + 'non_genesis_block.txt', 'r') as data:
            block = parse_block(data.read())
            self.assertFalse(block.is_root())

    def test_block_hash(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            string = data.read()
            block = parse_block(string)
            block_hash = str(hashlib.sha512(string.encode()).hexdigest())
            self.assertEqual(block.block_hash, block_hash)

    def test_decrypt_public_messages(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            string = data.read()
            block = parse_block(string)
            key_manager = get_test_key_manager()

            msg_list = ['Project Gutenberg’s The Complete Works of William Shakespeare, by William', 'Shakespeare',
                        'This eBook is for the use of anyone anywhere in the United States and',
                        'most other parts of the world at no cost and with almost no restrictions',
                        'whatsoever.  You may copy it, give it away or re-use it under the terms',
                        'of the Project Gutenberg License included with this eBook or online at',
                        'www.gutenberg.org.  If you are not located in the United States, you’ll',
                        'have to check the laws of the country where you are located before using', 'this ebook.',
                        'See at the end of this file: * CONTENT NOTE (added in 2017) *']

            self.assertEqual(msg_list, block.decrypt_messages(key_manager))


class TestMessageParsing(unittest.TestCase):
    message_data_path = 'tests/message_data/'
    message_tests = [
        ["parse_valid_public", "valid_public.txt", True],
        ["parse_random", "random.txt", False],
        ["parse_empty", "empty.txt", False],
        ["parse_empty_public_key", "empty_public_key.txt", False],
        ["parse_bad_public_key", "bad_public_key.txt", False],
        ["parse_empty_ds", "empty_ds.txt", False],
        ["parse_bad_ds", "bad_ds.txt", False],
        ["parse_empty_timestamp", "empty_timestamp.txt", False],
        ["parse_bad_timestamp", "bad_timestamp.txt", False],
        ["parse_empty_message_string", "empty_message_string.txt", True],
        ["parse_bad_message_string", "bad_message_string.txt", False],
        ['parse_private_msg_1', "valid_my_private.txt", True],
        ['parse_private_msg_2', "valid_private.txt", True]
    ]

    @staticmethod
    def generate_message_test(file, result):
        def test(self):
            with open(TestMessageParsing.message_data_path + file, 'r') as data:
                string = data.read()
                block = parse_message(string)
                if result:
                    self.assertTrue(block)
                else:
                    self.assertFalse(block)

        return test

    @staticmethod
    def setup_tests():
        for test in TestMessageParsing.message_tests:
            test_name = 'test_%s' % test[0]
            func = TestMessageParsing.generate_message_test(test[1], test[2])
            setattr(TestMessageParsing, test_name, func)

    def test_to_string(self):
        with open(TestMessageParsing.message_data_path + 'valid_public.txt', 'r') as data:
            string = data.read()
            self.assertEqual(repr(parse_message(string)), string)

    def test_parsing_data(self):
        with open(TestMessageParsing.message_data_path + 'valid_public.txt', 'r') as data:
            message = parse_message(data.read())
            self.assertEqual(message.create_time, 1520174648.2770298)
            self.assertEqual(message.message, "    By sovereignty of nature. First he was")
            self.assertEqual(message.recipient, None)
            self.assertIsNotNone(message.signature)

            with open(TestMessageParsing.message_data_path + "valid_public_sender_key.txt", 'r') as key:
                self.assertEqual(message.sender, key.read())

    def test_correct_signature(self):
        with open(TestMessageParsing.message_data_path + 'valid_public.txt', 'r') as data:
            message = parse_message(data.read())
            self.assertTrue(message.verify_signature())

    def test_private_correct_signature(self):
        with open(TestMessageParsing.message_data_path + 'valid_my_private.txt', 'r') as data:
            message = parse_message(data.read())
            self.assertTrue(message.verify_signature())

    def test_private_correct_signature2(self):
        with open(TestMessageParsing.message_data_path + 'valid_private.txt', 'r') as data:
            message = parse_message(data.read())
            self.assertTrue(message.verify_signature())

    def test_wrong_signature(self):
        with open(TestMessageParsing.message_data_path + 'public_wrong_signature.txt', 'r') as data:
            message = parse_message(data.read())
            self.assertFalse(message.verify_signature())

    def test_get_public_message(self):
        with open(TestMessageParsing.message_data_path + 'valid_public.txt', 'r') as data:
            message = parse_message(data.read())

            key_manager = get_test_key_manager()
            msg_str = message.get_message(key_manager)
            self.assertEqual("    By sovereignty of nature. First he was", msg_str)

    def test_get_my_private_message(self):
        with open(TestMessageParsing.message_data_path + 'valid_my_private.txt', 'r') as data:
            message = parse_message(data.read())

            key_manager = get_test_key_manager()
            msg_str = message.get_message(key_manager)
            self.assertEqual("TEST_RUA", msg_str)

    def test_get_private_message(self):
        with open(TestMessageParsing.message_data_path + 'valid_private.txt', 'r') as data:
            message = parse_message(data.read())

            key_manager = get_test_key_manager()
            msg_str = message.get_message(key_manager)
            self.assertIsNone(msg_str)

    def test_decrypt_public_message(self):
        with open(TestMessageParsing.message_data_path + 'valid_public.txt', 'r') as data:
            message = parse_message(data.read())

            key_manager = get_test_key_manager()
            msg_str = message.decrypt(key_manager.privatekey_eg)
            self.assertIsNone(msg_str)


def get_test_key_manager():
    return Keys(private, public, directory)


TestBlockParsing.setup_tests()
TestMessageParsing.setup_tests()
if __name__ == '__main__':
    unittest.main()
