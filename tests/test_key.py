import unittest

from key import Keys


class TestKeyLoading(unittest.TestCase):
    private = "tests/key_data/private_keys.pem"
    public = "tests/key_data/public_keys.pem"
    directory = "tests/key_data/key_directory.pem"

    def test_init_keys(self):
        keys = Keys(TestKeyLoading.private, TestKeyLoading.public, TestKeyLoading.directory)

        with open("tests/key_data/test_key1.txt", 'r') as test_key:
            data = test_key.read()
            self.assertIsNotNone(keys.look_up_private_keys(data))

        with open("tests/key_data/test_key2.txt", 'r') as test_key:
            data = test_key.read()
            self.assertIsNotNone(keys.look_up_private_keys(data))


if __name__ == '__main__':
    unittest.main()
