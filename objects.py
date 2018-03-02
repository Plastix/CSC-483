"""Parses and creates messages and blocks from strings."""
import re
import logging
from binascii import hexlify, unhexlify

from blockchain_constants import *

log = logging.getLogger('blockchain')

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

    def __init__(self, nonce, parent, create_time, miner, posts):
        """
        Takes data from a parsed block, deciphers them, and creates a Block.

        A Block has a starting nonce which is used to generate the proof-of-work
        hardness, the hash of its parent Block, the time the Block was created,
        the hash of the Block miner's public key, and a list of the posts
        attached to the Block. The list of posts is gauranteed to contain only
        validly formatted messages.

        WARNING: Constructor assumes data passed in is formatted properly and
        does NOT ensure the black is valid with regard to the blockchain.

        :param nonce: Nonce at beginning of block
        :param parent: Hash of the parent block
        :param create_time: Time the block was created
        :param miner: Hash of block miner's public key
        :param posts: Posts attached to the block

        :type nonce: int
        :type parent: str
        :type create_time: float
        :type miner: str
        :type posts: list

        :rtype: Block
        """
        self.nonce = nonce
        self.parent_hash = parent
        self.create_time = create_time
        self.miner_pub_key = miner
        self.posts = posts

    def __str__(self):
        posts_str = "\n"
        for post in self.posts:
            posts_str += "  |--{post}\n".format(post=post)
        ret_str = "Nonce: {nonce}\n" + \
        "Parent Hash: {parent}\n" + \
        "Creation Time: {create}\n" + \
        "Miner Hash: {miner}\n" + \
        "Posts: {posts}\n".format(nonce=self.nonce,
                                  parent=self.parent_hash,
                                  create=self.create_time,
                                  miner=self.miner_pub_key,
                                  posts=posts_str
                                  )

    def __repr__(self):
        ret_str = hexlify(self.nonce) + "|"
        ret_str += self.parent_hash + "|"
        ret_str += self.create_time + "|"
        ret_str += self.miner_pub_key
        for post in posts:
            ret_str += "|" + repr(post)
        return ret_str


def parse_message(msg_str):
    pass


def parse_block(block_str):
    """
    Parses the string form of a block into a Block object.

    Takes in any string, and if the string is properly formatted returns a
    corresponding Block object. If the string is not properly formatted, this
    method returns False. A properly formatted block string is '|' pipe
    delimited, with the first four parts being an int, a hex string, a float,
    and another hex string. This method also parses the accompanying messages,
    only including proprely formatted messages in the final list of messages
    attached to the block.

    :param block_str: The string representation of a block
    :type block_str: str
    :rtype: Block
    """
    block_parts = block_str.split('|')
    if len(block_parts) != 4 + MSGS_PER_BLOCK:
        return None

    try:
        nonce = int(block_parts[NONCE], 16)
    except ValueError:
        return None

    parent = block_parts[PARENT_HASH]
    if not is_hex(parent):
        return None

    try:
        created = float(block_parts[CREATE_TIME])
    except ValueError:
        return None

    miner = block_parts[BLOCK_MINER]
    if not is_hex(miner):
        return None

    # messages = list(filter(lambda x: x, map(parse_message, block_parts[4:])))

    return Block(nonce, parent, created, miner, messages)


def is_hex(hex_str):
    """Helper function to verify a string is a hex value."""
    return re.fullmatch('[0-9a-f]', hex_str)


def main():
    pass

if __name__ == '__main__':
    main()
