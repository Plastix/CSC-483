"""
Manage the keys and load keys from file to do verification.
"""

import hashlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


class Keys:

    def __init__(self, private_key_file, pub_key_file, key_directory):
        self.key_directory = key_directory
        self.pub_key_file = pub_key_file
        self.private_key_file = private_key_file
        self.table = {}  # internal table for my private/public keys

        self.pub_table = {}  # table that contains hash of public keys and pem of public keys
        self.publickey_main = None
        self.privatekey_main = None

        self.init_keys()

    def look_up_private_keys(self, public_key):
        if public_key in self.table:
            return self.table[public_key]
        return None

    def find_public_key_pem(self, hash):
        if hash in self.pub_table:
            return self.pub_table[hash]
        return None

    def init_keys(self):
        with open(self.private_key_file, 'rb') as private_keys:
            data = private_keys.read()
            key_pair_num = data.count(b"-----BEGIN PRIVATE KEY-----")

            for index in range(key_pair_num):
                private_key, private_key_str = load_key(data, index, True)
                with open(self.pub_key_file, 'rb') as public_keys:
                    public_key, public_key_str = load_key(public_keys.read(), index, False)

                # Found a valid key pair
                if public_key is not None and private_key is not None:
                    self.table[public_key_str.decode()] = private_key
                    self.publickey_main = public_key
                    self.privatekey_main = private_key

        with open(self.key_directory, 'rb') as key_directory:
            data = key_directory.read()
            key_num = data.count(b"-----BEGIN PUBLIC KEY-----")

            for index in range(key_num):
                public_key, public_key_str = load_key(data, index, False)
                public_key_hash = hashlib.sha256(public_key_str).hexdigest()
                self.pub_table[public_key_hash] = public_key

    def get_main_pub_key(self):
        return self.publickey_main.public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo
        )


def load_key(key_strings, num, private):
    if private:
        end_delim = b"-----END PRIVATE KEY-----\n"
    else:
        end_delim = b"-----END PUBLIC KEY-----\n"

    start_ix = 0
    end_ix = -1

    for i in range(num + 1):

        ix = key_strings.find(end_delim, start_ix)
        if ix < 0:
            # print("Error: Invalid key number")
            return None, None

        end_ix = ix + len(end_delim)
        key_str = key_strings[start_ix:end_ix]
        start_ix = end_ix

        if i == num:

            try:
                if private:
                    key = serialization.load_pem_private_key(
                        key_str,
                        password=None,
                        backend=default_backend()
                    )
                else:
                    key = serialization.load_pem_public_key(
                        key_str,
                        backend=default_backend()
                    )
                return key, key_str
            except:
                # print("Error: Invalid key file format")
                return None, None
    # print("Error: Invalid key file format")
    return None, None
