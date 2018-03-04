import logging
import unittest

from objects import parse_block


class TestParseMethods(unittest.TestCase):
    def test_to_string(self):
        with open('tests/data/valid_block.txt', 'r') as data:
            string = data.read()
            self.assertTrue(repr(parse_block(string)) == string)


parse_block_tests = [
    ["parse_valid_block", "valid_block.txt", True],
    ["parse_random", "random.txt", False],
    ["parse_empty", "empty.txt", False],
    ["parse_empty", "empty.txt", False],
    ["parse_empty_nonce", "empty_nonce.txt", False],
    ["parse_bad_nonce", "bad_nonce.txt", False],
]


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
