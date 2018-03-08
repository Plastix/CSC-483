import queue
import threading
import logging
import traceback
import sys
import time
import hashlib

from objects import parse_block, parse_message, Block, Message
from blockchain_constants import *
from key import Keys


class Blockchain(object):

    def __init__(self):
        """
        Responsible for initializing a Block object.

        The Blockchain object is responsible for keeping track of the state of
        the Blockchain as seen from the comptuer it is being run on as well as
        handling interactions with other peers on the blockchain network.

        blockchain_bbs.py creates a Blockchain object which it then passes to
        a Server object from network.py
        """

        self.log = logging.getLogger('blockchain')
        self.log.setLevel(logging.DEBUG)

        f_handler = logging.FileHandler('blockchain.log')
        f_handler.setLevel(logging.DEBUG)

        con_handler = logging.StreamHandler()
        con_handler.setLevel(logging.DEBUG)

        # Using Matt's log output format for consistency
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(formatter)
        con_handler.setFormatter(formatter)

        self.log.addHandler(f_handler)
        self.log.addHandler(con_handler)

        self.log.warning("=========== Blockchain logging started ==========")

        # Use this lock to protect internal data of this class from the
        # multi-threaded server.  Wrap code which modifies the blockchain with
        # "with self.lock:". Be careful not to nest these contexts or it will
        # cause deadlock.
        self.lock = threading.Lock()

        self.messages = []

        self.blocks = {}  # dictionary of hash(Block) -> BlockNode
        self.block_tree = None  # Tree of BlockNodes, points to the root
        self.latest_block = None  # BlockNode to mine on
        self.mined_block = None  # latest block mined by this blockchain.
        self.message_queue = queue.Queue()
        self.count = 0

        self.keys = Keys(private_key_file=PRIVATE_KEY_FILE,
                         pub_key_file=PUBLIC_KEY_FILE,
                         key_directory=KEY_DIRECTORY
                         )

    def get_message_queue_size(self):
        """
        Get the number of messages that are queued to be processed.

        This function returns the number of messages which the Blockchain
        object has received which have yet to be processed.

        This function is called by networking.py.
        """
        return self.message_queue.qsize()

    def add_message_str(self, msg_str):
        """
        Verifies then adds incoming messages to the message queue.

        This method takes a string containing a message received by the server
        from a peer or a user.  The message may be illformed, a duplicate, or
        invalid.  It first verifies that this is not the case, then adds the
        message to the queue of messages to be processed into the blockchain,
        and returns True. If the message is invalid, this method returns False.

        This function is called by networking.py.
        """

        message = parse_message(msg_str)

        # Make sure message string was properly formed
        if message is None:
            self.log.debug("Ill-formed message string")
            return False

        # Verify that the message is properly signed
        if not message.verify_signature():
            self.log.debug("Invalidly signed message string")
            return False

        # Verify that the message is not a duplicate
        with self.lock:
            if message in self.messages:
                self.log.debug("Duplicate message rejected")
                return False

        # Add message to message queue
        self.message_queue.put(message)

        return True

    def add_block_str(self, block_str):
        """
        Verifies then adds incoming blocks to the blockchain.

        This method takes a string containing a block received by the server
        from a peer or a user.  The block may be ill-formed, a duplicate, or
        invalid.  It first verifies that this is not the case, then adds the
        block to the blockchain and returns True. If the block is invalid, this
        method returns False.

        This function is called by networking.py.
        """
        block = parse_block(block_str)
        if block is None:
            self.log.debug("Block ill-formed")
            return False

        if not block.verify_pow():
            self.log.debug("Block invalid")
            return False

        if block.parent_hash not in self.blocks and not block.is_root():
            self.log.debug("Block has non-existent parent")
            return False

        if block.block_hash in self.blocks:
            self.log.debug("Block is a duplicate")
            return False

        with self.lock:
            return self._add_block(block)

    def _add_block(self, block, root=False):
        """
        Adds a Block object to the Blockchain and updates the chain.

        The Block is put into a BlockNode and added as a child to its parent
        BlockNode. Its Messages are added to the current messages list if the
        parent is the latest block. If the parent is not the latest Block, we
        traverse the BlockNode tree up from this new node and update our
        message tracker with the messages therein.

        WARNING: Certainly not thread safe.

        :param block: The Block object to add
        :return: Success of adding the Block
        """
        if block.is_root():
            block_node = BlockNode(block, None)
            self.blocks[block.block_hash] = block_node
            self.block_tree = block_node
            self.log.debug("Added block as root")
        else:
            parent_node = self.blocks[block.parent_hash]
            block_node = BlockNode(block, parent_node)
            self.blocks[block.block_hash] = block_node
            parent_node.add_child(block_node)
            self.log.debug("Added block to blockchain")

        # TODO Message duplicate checking

        return True

    def get_new_block_str(self):
        """
        Get the latest mined block if one exists.

        This method returns the string encoding of a newly mined block if it
        such a block exists, and otherwise returns None. This is a NON-BLOCKING
        function, it returns immediately without waiting for a new block to be
        mined.

        This function is called by networking.py.
        """
        with self.lock:
            return repr(self.mined_block) if self.mined_block else None

    def get_all_block_strs(self, t):
        """
        Get the string representation of every block in the chain after time t.

        This method returns a list of the string encoding of each of the blocks
        in this blockchain, including ones not on the main chain, whose
        timestamp is greater then the parameter t.

        This function is called by networking.py.
        """
        block_strs = []

        if self.block_tree is not None:
            next_nodes = [self.block_tree]
            while len(next_nodes) > 0:
                cur_node = next_nodes.pop(0)
                next_nodes += cur_node.children
                if cur_node.get_time > t:
                    block_strs.append(repr(cur_node.block))
        return block_strs

    def mine(self):
        """
        Mine a new block featuring the latest incoming messages.

        This method waits for enough messages to be received from the server,
        then forms them into blocks, mines the block, adds the block to the
        blockchain, and prepares the block to be broadcast by the server.
        The mining of a block may be interrupted by a superceding
        add_block_str() call.  In this case the miner should do its best to
        move on to mine another block and not lose any messages it was
        previously attempting to mine.  This process repeats forever, and this
        function never runs.

        This function is called in blockchain_bbs.py as a new thread.
        """

        while True:
            # Make sure we have enough new messages in the queue
            # if self.message_queue.qsize() < MSGS_PER_BLOCK:
            #     continue
            #
            # # Note that this is a list of Message objects
            # message_list = list(self.message_queue.queue)[:10]
            #
            #
            # mined_block = Block(nonce=0,
            #                     parent=hash(self.latest_block),
            #                     create_time=time.time(),
            #                     miner=hashlib.sha256().hexdigest())
            pass



class BlockNode(object):
    """
    Holds a single block in the Blockchain tree.

    Contains the parent block if one exists and children blocks if they exist.
    Each block must have exactly one parent unless it is the root node. The hash
    of the Block in question is also considered the hash of the BlockNode.
    """

    def __init__(self, block, parent):
        """
        Construct the BlockNode given a Block and the BlockNode of its parent.

        :param block: The Block which this node holds
        :param parent: The parent BlockNode representing the parent Block
        """
        self.parent = parent
        self.block = block
        self.children = []

    def add_child(self, child):
        """Add a child BlockNode"""
        self.children.append(child)

    @property
    def get_time(self):
        """Return the Block's time of creation."""
        return self.block.create_time