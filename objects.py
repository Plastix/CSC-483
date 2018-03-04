"""Parses and creates messages and blocks from strings."""
import hashlib
import re
import logging
import binascii
from binascii import hexlify, unhexlify

from blockchain_constants import *

log = logging.getLogger('blockchain')


class Message(object):
    """Represents a message on the chain."""

    def __init__(self, sender, create_time, message, signature, recipient=None):
        """
        Takes data from a parsed message, deciphers, and creates message.

        A Message can be either public or private. If public, it contains an
        unencrypted message, whereas if it's private then it contains an
        encrypted message and the public key of the recipient. All messages
        also have the poster's public key, the time created, and a digital
        signature from the poster.

        WARNING: Constructor assumes data passed in is formatted properly and
        does NOT ensure the message is valid with regard to the blockchain.

        :param sender: The message sender's private key
        :param create_time: Time the message was created
        :param message: The text of the message being sent
        :param signatue: A digital signature of the message by its sender
        :param recipient: The public key of the recipient if message is private

        :type sender: str
        :type create_time: float
        :type message: str
        :type signature: str
        :type posts: list

        :rtype: Message
        """
        self.sender = sender
        self.create_time = create_time
        self.message = message
        self.signature = signature
        self.recipient = recipient

    def __str__(self):
        ret_str = "Sender Key: {sender}\n" + \
                  "Creation Time: {create}\n" + \
                  "Message: {message}\n"
        ret_str = ret_str.format(sender=self.sender,
                                 create=self.create_time,
                                 message=self.message)
        if self.recipient:
            ret_str += "Recipient Key: {recipient}\n"
            ret_str = ret_str.format(recipient=self.recipient)
        return ret_str

    def __repr__(self):
        body_str = "{time}:{text}".format(time=self.create_time,
                                          text=hexlify(self.message.encode()).decode()
                                          )
        if self.recipient:
            body_str += ":{rcp}".format(rcp=hexlify(self.recipient.encode()).decode())

        return "{send}&{body}&{sig}".format(send=hexlify(self.sender.encode()).decode(),
                                            body=body_str,
                                            sig=hexlify(self.signature).decode()
                                            )


class Block(object):

    def __init__(self, nonce, parent, create_time, miner, posts):
        """
        Takes data from a parsed block, deciphers them, and creates a Block.

        A Block has a starting nonce which is used to generate the proof-of-work
        hardness, the hash of its parent Block, the time the Block was created,
        the hash of the Block miner's public key, and a list of the posts
        attached to the Block. The list of posts is guaranteed to contain only
        validly formatted messages.

        WARNING: Constructor assumes data passed in is formatted properly and
        does NOT ensure the block is valid with regard to the blockchain.

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
        self.miner_key_hash = miner
        self.posts = posts

    def __str__(self):
        posts_str = "\n"
        for post in self.posts:
            posts_str += "  |--{post}\n".format(post=post)
        ret_str = "Nonce: {nonce}\n" + \
                  "Parent Hash: {parent}\n" + \
                  "Creation Time: {create}\n" + \
                  "Miner Hash: {miner}\n" + \
                  "Posts: {posts}\n"
        return ret_str.format(nonce=self.nonce,
                              parent=self.parent_hash,
                              create=self.create_time,
                              miner=self.miner_key_hash,
                              posts=posts_str
                              )

    def __repr__(self):
        ret_str = hex(self.nonce)[2:] + "|"
        ret_str += self.parent_hash + "|"
        ret_str += self.miner_key_hash + "|"
        ret_str += str(self.create_time)
        for post in self.posts:
            ret_str += "|" + repr(post)
        return ret_str

    def verify_pow(self):
        # TODO
        block_hash = hashlib.sha512(repr(self)).hexdigest()
        print(block_hash)


def parse_message(msg_str):
    """
    Parses the string form of a message into a Message object.

    Takes in any string, and if the string is properly formatted returns a
    corresponding Message object. If the string is not properly formatted, this
    method returns False.

    :param msg_str: The string representation of a block
    :type msg_str: str
    :rtype: Message
    """

    # Split the message
    msg_parts = msg_str.split("&")
    # Check message is appropriate length
    if len(msg_parts) != 3:
        log.warning("Error parsing message: Length %s invalid", len(msg_parts))
        return None

    # Split the message body
    msg_body_parts = msg_parts[MSG_BODY].split(":")
    # Check the body is the right length
    if not 1 < len(msg_body_parts) < 3:
        log.warning("Error parsing message: Body length %s invalid", len(msg_body_parts))
        return None

    # Get the message sender's public key
    sender_key = msg_parts[SENDER_KEY]
    # Check that it's not the empty string
    if sender_key == '':
        log.warning("Error parsing message: sender key is empty")
        return None
    # Unhexlify the sender key
    try:
        sender_key = unhexlify(sender_key).decode()
    except binascii.Error:
        log.warning("Error parsing message: Invalid sender key: %s", msg_parts[SENDER_KEY])
        return None
    print(sender_key)

    # Get the message creation time
    create_time = msg_body_parts[MSG_TIME]
    # Convert to a float
    try:
        create_time = float(msg_body_parts[MSG_TIME])
    except ValueError:
        log.warning("Error parsing message: Invalid create time %s", create_time)
        return None
    print(create_time)

    # Get the text of the message
    message_str = msg_body_parts[MSG_TEXT]
    try:
        message_str = unhexlify(message_str).decode()
    except binascii.Error:
        log.warning("Error parsing message: Invalid message string %s", msg_body_parts[MSG_TEXT])
        return None
    print(message_str)

    # If the message is private, get the recipient's public key
    if len(msg_body_parts) == 3:
        # Get the recipient's key
        recipient_key = msg_body_parts[MSG_PUB_KEY]
        # Check that its not empty
        if recipient_key == '':
            log.warning("Error parsing message: empty recipient key")
            return None
        # Then convert to a string
        try:
            recipient_key = unhexlify(recipient_key).decode()
        except binascii.Error:
            log.warning("Error parsing message: Invalid recipient key %s", recipient_key)
            return None
    else:
        recipient_key = None

    # Get the digital signature of the sender for the message
    message_sig = msg_parts[MSG_SIG]
    # Check that it's not empty
    if message_sig == '':
        log.warning("Error parsing message: empty signature")
        return None
    # Turn it to a string
    try:
        message_sig = unhexlify(msg_parts[MSG_SIG])
    except binascii.Error:
        log.warning("Error parsing message: Invalid signature %s", msg_parts[MSG_SIG])
        return None

    return Message(sender_key, create_time, message_str, message_sig, recipient_key)


def parse_block(block_str):
    """
    Parses the string form of a block into a Block object.

    Takes in any string, and if the string is properly formatted returns a
    corresponding Block object. If the string is not properly formatted, this
    method returns False. A properly formatted block string is '|' pipe
    delimited, with the first four parts being an int, a hex string, a float,
    and another hex string. This method also parses the accompanying messages,
    only including properly formatted messages in the final list of messages
    attached to the block.

    :param block_str: The string representation of a block
    :type block_str: str
    :rtype: Block
    """
    block_parts = block_str.split('|')
    if len(block_parts) != 4 + MSGS_PER_BLOCK:
        log.info("Error parsing block: Length %s invalid", len(block_parts))
        return None

    nonce = block_parts[NONCE]
    try:
        nonce = int(nonce, 16)
    except ValueError:
        log.info("Error parsing block: Invalid nonce %s", nonce)
        return None

    parent = block_parts[PARENT_HASH]
    if not is_hex(parent):
        log.info("Error parsing block: parent hash is not hex: %s", parent)
        return None

    created = block_parts[CREATE_TIME]
    try:
        created = float(block_parts[CREATE_TIME])
    except ValueError:
        log.info("Error parsing block: Invalid creation time %s", created)
        return None

    miner = block_parts[BLOCK_MINER]
    if not is_hex(miner):
        log.info("Error parsing block: miner hash is not hex: %s", miner)
        return None

    messages = list(filter(lambda x: x is not None, map(parse_message, block_parts[MESSAGE_START:])))

    return Block(nonce, parent, created, miner, messages)


def is_hex(hex_str):
    """Helper function to verify a string is a hex value."""
    return re.fullmatch('[0-9a-f]+', hex_str)
