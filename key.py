"""
Manage the keys and load keys from file to do verification.
"""

from blockchain import *
from network import *
from blockchain_constants import *
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import hashlib


class Keys:

    def __init__(self, f):
        # internal table for my private/public keys
        self.table = {}
        # table that contains hash of public keys and pem of public keys
        self.pub_table = {}
        self.publickey_eg = None
        self.privatekey_eg = None

        # building the internal key table
        with open("private_keys.pem", "rb") as private_keys:
            #code basically identical to send_message

            text = private_keys.read()
            end_delim = b"-----END PRIVATE KEY-----\n"

            start_ix = 0
            end_ix = -1

            while True:
                ix = text.find(end_delim, start_ix)
                if ix < 0:
                    break

                end_ix = ix + len(end_delim)
                key_str = text[start_ix:end_ix]
                start_ix = end_ix

                private_key = serialization.load_pem_private_key(
                    key_str,
                    password=None,
                    backend=default_backend())

                public_key = private_key.public_key()

                public_key_pem = public_key.public_bytes(
                                    encoding=serialization.Encoding.PEM,
                                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                                    )
                self.table[public_key_pem] = private_key

                if self.publickey_eg == None:
                    self.publickey_eg = public_key_pem
                    self.privatekey_eg  = private_key

        with open("public_keys.pem", "rb") as public_keys:

            text = public_keys.read()
            end_delim = b"-----END PUBLIC KEY-----\n"

            start_ix = 0
            end_ix = -1
            while True:
                ix = text.find(end_delim, start_ix)
                if ix < 0:
                    break

                end_ix = ix + len(end_delim)
                key_str = text[start_ix:end_ix]
                start_ix = end_ix

                public_key_pem = serialization.load_pem_public_key(
                            key_str,
                            backend=default_backend()
                        )
                public_key_hash = hashlib.sha256(public_key_pem).hexdigest()

                self.pub_table[public_key_hash] = public_key_pem


    def look_up_private_keys(self, public_key):
        if public_key in self.table:
            return self.table[public_key]
        return None

    def find_public_key_pem(self, hash):
        if hash in self.pub_table:
            return self.pub_table[hash]
        return None
