import unittest

from objects import parse_block

parse_block_tests = [
    ["parse_valid_block", "valid_block.txt", True],
    ["parse_random", "random.txt", False],
    ["parse_empty", "empty.txt", False],
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


class TestParseMethods(unittest.TestCase):
    def test_to_string(self):
        with open('tests/data/valid_block.txt', 'r') as data:
            string = data.read()
            self.assertEquals(repr(parse_block(string)), string)

    def test_parsing_data(self):
        with open('tests/data/valid_block.txt', 'r') as data:
            block = parse_block(data.read())
            print(block)
            self.assertEquals(block.nonce, 280815619281315998298257152433917011173307790385)
            self.assertEquals(block.parent_hash, "000000000000000000000000000000000000")
            self.assertEquals(block.create_time, 1519773893.9249759)
            self.assertEquals(block.miner_key_hash, "03586f81a493d12fc4c71a01d648f83ac5d544e7168f96dcc32fa6bd4d54992e")
            # TODO Verify messages are correct


def generate_block_test(file, result):
    def test(self):
        if result:
            self.assertTrue(parse(file))
        else:
            self.assertFalse(parse(file))

    return test


def setup_tests():
    for test in parse_block_tests:
        test_name = 'test_%s' % test[0]
        func = generate_block_test(test[1], test[2])
        setattr(TestParseMethods, test_name, func)


def parse(file):
    with open('tests/data/' + file, 'r') as file:
        data = file.read()
        return parse_block(data)


setup_tests()
if __name__ == '__main__':
    unittest.main()
