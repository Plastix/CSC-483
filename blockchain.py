import hashlib
import logging
import os
import queue
import random
import threading
import time

from blockchain_constants import *
from key import Keys
from objects import parse_block, parse_message, Block


class Blockchain(object):

    def __init__(self, ledger_file, message_file, stats_file):
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

        f_handler = logging.FileHandler('miner.log')
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

        self.keys = Keys(private_key_file=PRIVATE_KEY_FILE,
                         pub_key_file=PUBLIC_KEY_FILE,
                         key_directory=KEY_DIRECTORY
                         )

        self.message_file = message_file
        self.ledger_file = ledger_file
        self.stats_file = stats_file
        self._create_empty_files()

        # Use this lock to protect internal data of this class from the
        # multi-threaded server.  Wrap code which modifies the blockchain with
        # "with self.lock:". Be careful not to nest these contexts or it will
        # cause deadlock.
        self.lock = threading.Lock()

        self.blocks = {}  # dictionary of Block.hash -> BlockNode
        self.block_tree = None  # Tree of BlockNodes, points to the root
        self.latest_block = None  # BlockNode to mine on
        self.second_longest_chain = None
        self.mined_block = None  # latest block mined by this blockchain.
        self.latest_time = 0  # Timestamp of latest_block
        self.total_blocks = 0  # Total blocks in our blockchain
        self.readable_messages = 0  # Number of messages we can read

        self.messages = {}  # dictionary of Message -> boolean
        self.message_queue = queue.Queue()

        self._load_saved_ledger()

    def _create_empty_files(self):
        # Create empty ledger file if one dos not exist
        self._create_empty_file(self.ledger_file)

        self._create_empty_file(self.message_file)
        # Clear message file
        open(self.message_file, 'w').close()

        self._create_empty_file(self.stats_file)

    def _create_empty_file(self, file):
        if not os.path.exists(file):
            self.log.debug("Creating empty file %s!", file)
            with open(file, 'w'):
                pass

    def _load_saved_ledger(self):
        """
        Reads saved block strings from local ledger.txt. This stops us from having to requery all peers to get the
        entire version history. networking.py uses self.latest_time to do the correct fetch. This time is updated in
        self.add_block_str
        """

        with open(self.ledger_file, 'r') as ledger:
            blocks = ledger.read().strip().splitlines()
            if len(blocks) != 0:
                self.log.debug('Loading blocks from local ledger!')
            for block_str in blocks:
                self._add_block_str(block_str, False)

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
            # TODO Don't add a message to the queue that isn't already in the queue
            # This only checks if messages are in the current blockchain
            if message in self.messages:
                self.log.debug("Duplicate message rejected")
                return False

        # Add message to message queue
        self.log.debug("Adding message to message queue!")
        self.message_queue.put(message)

        return True

    def _add_block_str(self, block_str, write_to_ledger=True):
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
            return self._add_block(block, write_to_ledger)

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

        return self._add_block_str(block_str)

    def _update_latest_pointers(self, block_node):
        if block_node.depth > self._get_current_depth():
            self.second_longest_chain = self.latest_block
            self.latest_time = block_node.create_time
            self.latest_block = block_node
        elif block_node.depth > self._get_fork_depth():
            self.second_longest_chain = block_node

    def _add_block(self, block, write_to_ledger):
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

        # Block contains at least one duplicate message so don't add it
        if any(map(self._is_duplicate_message, block.posts)):
            return False

        if block.is_root():
            block_node = BlockNode(block, None)
            self.block_tree = block_node
            self.log.debug("Added block as root")
            self._update_latest_pointers(block_node)
        else:
            parent_node = self.blocks[block.parent_hash]
            block_node = BlockNode(block, parent_node)
            parent_node.add_child(block_node)
            old_latest = self.latest_block.block.block_hash

            # Check if the new block makes a longer chain and switch to it
            self._update_latest_pointers(block_node)

            # We moved branches, update message table
            if self.latest_block.block.parent_hash != old_latest:
                self._reinit_message_table(block.parent_hash)

        # Add all new posts to message table
        self._add_block_msgs(block)
        self._write_new_messages(block)

        self.log.debug("Added block to blockchain")
        self.blocks[block.block_hash] = block_node

        self.total_blocks += 1

        # Update ledger.txt with newly added block
        if write_to_ledger:
            # self.log.warning("Writing to ledger!")
            with open(self.ledger_file, 'a') as ledger:
                ledger.write(repr(block) + "\n")

        if self.total_blocks % 10 == 0:
            self._write_stats_file()

        return True

    def _add_block_msgs(self, block):
        for msg in block.posts:
            self.messages[repr(msg)] = True

    def _write_new_messages(self, block):
        with open(self.message_file, 'a') as message_file:
            message_file.write("\n")

            messages = block.decrypt_messages(self.keys)
            self.readable_messages += len(messages)
            message_file.write("\n".join(messages))

    def _reinit_message_table(self, parent_hash):
        self.messages.clear()
        block_node = self.blocks[parent_hash]

        messages = []
        while block_node is not None:
            self._add_block_msgs(block_node.block)
            block_node = block_node.parent
            messages.extend(block_node.block.decrypt_messages(self.keys))

        messages.reverse()
        self.readable_messages = len(messages)
        string = '\n'.join(messages)

        with open(self.message_file, 'w') as message_file:
            message_file.write("\n")
            message_file.write(string)

    def _is_duplicate_message(self, message):
        msg_str = repr(message)
        if message in self.messages:
            return self.messages[msg_str]
        return False

    def _get_current_depth(self):
        return self.latest_block.depth if self.latest_block is not None else 0

    def _get_fork_depth(self):
        return self.second_longest_chain.depth if self.second_longest_chain is not None else 0

    def get_new_block_str(self):
        """
        Get the latest mined block if one exists.

        This method returns the string encoding of a newly mined block if it
        such a block exists, and otherwise returns None. This is a NON-BLOCKING
        function, it returns immediately without waiting for a new block to be
        mined.

        This function is called by networking.py.
        """
        # TODO do we need a lock here??
        with self.lock:
            if self.mined_block is not None:
                string = repr(self.mined_block)
                self.mined_block = None
                return string
            return None

    def _write_stats_file(self):
        with open(self.stats_file, 'w') as stats:
            stats.write("Readable messages: %s\n" % self.readable_messages)
            stats.write("Longest chain: %d\n" % self._get_current_depth())
            stats.write("Stale blocks: %d\n" % (self.total_blocks - self._get_current_depth()))
            stats.write("Longest fork: %d\n" % self._get_fork_depth())

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
            if self.message_queue.qsize() < MSGS_PER_BLOCK:
                continue

            self.log.debug("Starting to mine a block!")
            # Note that this is a list of Message objects
            message_list = [self.message_queue.get() for _ in range(MSGS_PER_BLOCK)]

            while True:
                nonce = random.getrandbits(NONCE_BIT_LENGTH)
                block = Block(nonce=nonce,
                              parent=self.latest_block.block.block_hash,
                              create_time=time.time(),
                              miner=str(hashlib.sha256().hexdigest()),
                              posts=message_list)

                if block.verify_pow():
                    self.mined_block = block
                    block_str = repr(block)
                    self.log.debug("!!! Mined a block !!!\n%s", block_str)
                    self._add_block(block, write_to_ledger=True)
                    break


class BlockNode(object):
    """
    Holds a single block in the Blockchain tree.

    Contains the parent block if one exists and children blocks if they exist.
    Each block must have exactly one parent unless it is the root node. The hash
    of the Block in question is also considered the hash of the BlockNode.
    """

    def __init__(self, block: Block, parent: object):
        """
        Construct the BlockNode given a Block and the BlockNode of its parent.

        :param block: The Block which this node holds
        :param parent: The parent BlockNode representing the parent Block
        """
        self.parent = parent
        self.block = block
        self.children = []
        self.depth = 1 if parent is None else parent.depth + 1

    def add_child(self, child):
        """Add a child BlockNode"""
        self.children.append(child)

    @property
    def get_time(self):
        """Return the Block's time of creation."""
        return self.block.create_time
