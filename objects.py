"""Parses and creates messages and blocks from strings."""

def parse_message(str):
    pass

def parse_block(str):
    pass


class Message(object):
    """Represents a message on the chain."""

    def __init__(self, arg):
        """
        Takes data from a parsed message, deciphers, and creates message.

        Assume data passed in is formatted properly. Does not ensure blockchain
        validity.
        """
        self.arg = arg



class Block(object):

    def __init__(self, nonce, parent_hash, time, miner, posts):
        """
        Takes data from a parsed block, deciphers them, and creates a Block.

        Assume data passed in is formatted properly. Does not ensure blockchain
        validity.
        """
        self.nonce = nonce
