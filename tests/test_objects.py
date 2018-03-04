import unittest

from objects import parse_block, parse_message


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
            self.assertEquals(repr(parse_block(string)), string)

    def test_parsing_data(self):
        with open(TestBlockParsing.block_data_path + 'valid_block.txt', 'r') as data:
            block = parse_block(data.read())
            print(block)
            self.assertEquals(block.nonce, 280815619281315998298257152433917011173307790385)
            self.assertEquals(block.parent_hash, "000000000000000000000000000000000000")
            self.assertEquals(block.create_time, 1519773893.9249759)
            self.assertEquals(block.miner_key_hash, "03586f81a493d12fc4c71a01d648f83ac5d544e7168f96dcc32fa6bd4d54992e")
            # TODO Verify messages are correct


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
            self.assertEquals(repr(parse_message(string)), string)

    def test_parsing_data(self):
        # TODO write this
        self.fail()


TestBlockParsing.setup_tests()
TestMessageParsing.setup_tests()
if __name__ == '__main__':
    unittest.main()
