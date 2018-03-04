import unittest
from objects import parse_block


class TestParseMethods(unittest.TestCase):

    def test_parse_valid_block(self):
        self.assertTrue(parse("valid_block.txt"), "No block returned!")

    def test_parse_random(self):
        self.assertFalse(parse("random.txt"))


def parse(file):
    with open('tests/data/' + file, 'r') as file:
        data = file.read()
        return parse_block(data)


if __name__ == '__main__':
    unittest.main()
