import hashlib
import logging
import os
import random
import threading
import time
from typing import List
from binascii import hexlify

from blockchain_constants import *
from key import Keys
from objects import parse_block, parse_message, Block, get_collusion_message


class MessageQueue(List):

    def __contains__(self, item):
        return repr(item) in map(repr, self)


class Blockchain(object):

    num_trees = 0
    fork_counter = 0
    fork_lengths = {0: 0}

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

        self.miner_id = str(hashlib.sha256(self.keys.get_main_pub_key()).hexdigest())

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
        self.root = None
        self.latest_block = None  # BlockNode to mine on
        self.second_longest_chain = None
        self.mined_block = None  # latest block mined by this blockchain.
        self.latest_time = 0  # Timestamp of latest_block
        self.last_update = 0
        self.total_blocks = 0  # Total blocks in our blockchain
        self.mining_flag = GIVEN_BLOCK
        self.message_list = [get_collusion_message(self.keys) for _ in range(MSGS_PER_BLOCK)]
        self.max_depth = 0
        self.messages = set()
        self.message_num = 0
        self.last_msg_update = 0
        self.rejects = {}

        self.message_queue = MessageQueue()

        self._load_saved_ledger()

    def _create_empty_files(self):
        # Create empty ledger file if one dos not exist
        self._create_empty_file(self.ledger_file)

        self._create_empty_file(self.message_file)
        # Clear message file
        open(self.message_file, 'w').close()

        self._create_empty_file(self.stats_file)

        self._create_empty_file('peers.txt')

    def _create_empty_file(self, file):
        if not os.path.exists(file):
            self.log.debug("Creating empty file %s!", file)
            with open(file, 'w'):
                pass

    def _load_saved_ledger(self):
        """
        Reads saved block strings from local ledger.txt. This stops us from having to re-query peers to get the
        entire version history. networking.py uses self.latest_time to do the correct fetch. This time is updated in
        self.add_block_str
        """

        with open(self.ledger_file, 'r') as ledger:
            self.log.debug('Loading blocks from local ledger!')
            i = 0
            for block_str in ledger:
                i += 1
                if self._add_block_str(block_str.strip(), False):
                    self.log.info("Loaded block %d", i)

        # After loading all blocks from file, tell our miner to continue
        self.last_update = self.latest_time
        self.mining_flag = CONTINUE_MINING

    def get_message_queue_size(self):
        """
        Get the number of messages that are queued to be processed.

        This function returns the number of messages which the Blockchain
        object has received which have yet to be processed.

        This function is called by networking.py.
        """
        with self.lock:
            return len(self.message_queue)

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
            if message in self.message_queue:
                self.log.debug("Duplicate message rejected (already in message queue)")
                return False

            # This only checks if messages are in the current blockchain
            if self._is_duplicate_message(message):
                self.log.debug("Duplicate message rejected (already in blockchain)")
                return False

            # Add message to message queue
            self.log.debug("Adding message to message queue!")
            self.message_queue.append(message)

            return True

    def _add_block_str(self, block_str, write_to_ledger=True, mined_ourselves=False):
        block = parse_block(block_str)
        if block is None:
            self.log.debug(RED + "%s - Block ill-formed" + NC, block.miner_key_hash[:5])
            self.rejects[block.block_hash] = "ill-formed"
            return False

        if not block.verify_pow():
            self.log.debug(RED + "%s - Block invalid POW" + NC + "\n\t%s", block.miner_key_hash[:5], repr(block))
            self.rejects[block.block_hash] = "invalid POW"
            return False

        if block.parent_hash not in self.blocks and not block.is_root():
            self.log.debug("%s - Block has non-existent parent", block.miner_key_hash[:5])
            if block.parent_hash in self.rejects:
                self.log.warning("\t" + RED + "Block parent %s in rejected: %s" + NC, block.parent_hash, self.rejects[block.parent_hash])
            self.rejects[block.block_hash] = "non-existent parent"
            return False

        if block.block_hash in self.blocks:
            self.log.debug(RED + "%s - Block is a duplicate" + NC, block.miner_key_hash[:5])
            return False

        return self._add_block(block, write_to_ledger, mined_ourselves)

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
        return self._add_block_str(block_str, True, False)

    def _update_latest_pointers(self, block_node):
        if block_node.depth > self.max_depth:
            self.latest_block = block_node
            self.max_depth = block_node.depth

    def _add_block(self, block: Block, write_to_ledger, mined_ourselves):
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

        with self.lock:
            self.mining_flag = GIVEN_BLOCK

        with self.lock:
            if block.parent_hash in self.blocks:
                parent_node = self.blocks[block.parent_hash]
                block_node = BlockNode(block, parent_node)
                parent_node.add_child(block_node)

                self._update_latest_pointers(block_node)  # Check if the new block makes a longer chain and switch to it

                self.log.debug(GREEN + "%s:[%s] added block to fork %d at depth %d" + NC, block.miner_key_hash[:6], time.ctime(block.create_time), block_node.fork_num, block_node.depth)
                # self.log.debug("Added block to blockchain")
            elif block.is_root:
                block_node = BlockNode(block, None)
                self.root = block_node
                # self.log.debug("Added block as root")
                self.log.debug(GREEN + "%s:[%s] added block as root %d" + NC, block.miner_key_hash[:6], time.ctime(block.create_time), block_node.tree_num)
                self._update_latest_pointers(block_node)
                # self.messages.clear()
                Blockchain.num_trees += 1

            self._add_block_msgs(block)  # Add all new posts to message table
            if self.message_num % 10000 == 0:
                self._write_new_messages(self.message_num-10000)  # Save new messages to file
            self.blocks[block.block_hash] = block_node
            self.total_blocks += 1

            # Update ledger.txt with newly added block
            if write_to_ledger:
                with open(self.ledger_file, 'a') as ledger:
                    ledger.write(repr(block) + "\n")

            if self.total_blocks % STATS_UPDATE_INTERVAL == 0:  # Every few blocks update stats.txt
                self._write_stats_file()

            self.mining_flag = CONTINUE_MINING

            if not mined_ourselves:
                self._update_msg_queue(block)

            if time.time() - self.last_msg_update > MSG_UPDATE_DELAY:
                self._reinit_message_table()
                self.last_msg_update = time.time()

            return True

    def _add_block_msgs(self, block):
        for msg in block.posts:
            self.messages.add(repr(msg))
            self.message_num += 1

    def _write_new_messages(self, last_i):
        with open(self.message_file, 'a') as message_file:
            message_file.write("\n".join(list(self.messages)[last_i:]))

    def _reinit_message_table(self):
        self.messages = set()
        self.message_num = 0
        block_node = self.blocks[self.latest_block.get_hash]

        while block_node is not None:
            self._add_block_msgs(block_node.block)
            self._update_msg_queue(block_node)
            block_node = block_node.parent

        # self.messages.reverse()
        msg_str = "\n".join(self.messages)

        with open(self.message_file, 'w') as message_file:
            message_file.write("\n")
            message_file.write(msg_str)

    def _is_duplicate_message(self, message):
        return repr(message) in self.messages

    def _get_current_depth(self):
        if len(Blockchain.fork_lengths) == 0:
            return 0
        return max(Blockchain.fork_lengths.values())

    def _get_fork_depth(self):
        if len(Blockchain.fork_lengths) < 2:
            return 0
        return sorted(Blockchain.fork_lengths.keys(), key=lambda x: Blockchain.fork_lengths[x])[1]

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
            if self.mined_block is not None:
                string = repr(self.mined_block)
                self.mined_block = None
                self.log.debug("Gave server mined block!")
                return string
            return None

    def _write_stats_file(self):
        with open(self.stats_file, 'w') as stats:
            stats.write("Readable messages: %s\n" % self.message_num)
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
        with self.lock:
            block_strs = []

            next_nodes = [self.root]
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
        self.log.debug("Miner %s : Mining on thread %d", self.miner_id[:6], threading.get_ident() % 10000)
        while True:
            # Make sure we have enough new messages in the queue
            if self.get_message_queue_size() < MSGS_PER_BLOCK:
                continue

            self.log.info("Thread: %d - "+ RED +"Starting to mine a block!" + NC, threading.get_ident() % 10000)

            with self.lock:
                if self.message_list is None:
                    self.message_list = [self.message_queue.pop(0) for i in range(MSGS_PER_BLOCK)]

            while self.mining_flag != CONTINUE_MINING or self.latest_block is None:
                pass

            while self.mining_flag == CONTINUE_MINING:
                nonce = hexlify(str(random.getrandbits(NONCE_BIT_LENGTH)).encode()).decode()

                # Parent hash is 64 '0's if we are mining the genesis block
                parent_hash = self.latest_block.block.block_hash if self.latest_block is not None else '0' * 36

                block = Block(nonce=nonce,
                              parent=parent_hash,
                              create_time=time.time(),
                              miner=self.miner_id,
                              posts=self.message_list)

                if block.verify_pow():
                    self.log.info("Thread: %d - " + GREEN + "Mined a block !!!" + NC + "\n", threading.get_ident() % 10000)
                    self.mined_block = block
                    self._add_block(block, write_to_ledger=True, mined_ourselves=True)
                    self.message_list = None
                    break

            if self.mining_flag == GIVEN_BLOCK:
                self.log.debug("Mining interrupted - given a block from a peer")
                self._add_all_to_message_queue(self.message_list)
            self.mining_flag = CONTINUE_MINING

    def _add_all_to_message_queue(self, msgs):
        with self.lock:
            for msg in msgs:
                if msg not in self.message_queue and msg not in self.latest_block.block.posts:
                    self.message_queue.append(msg)

    def _update_msg_queue(self, block):
        for msg in block.posts:
            if msg in self.message_queue:
                try:
                    self.message_queue.remove(msg)
                except ValueError:
                    self.log.warning(
                        "Attempted to remove msg from message queue (not in queue!)")

    def generate_dot_file(self):
        """
        Generates a .gv file for displaying the blockchain.
        """
        dot_text = "digraph blockchain {"
        frontier = [self.root]
        while frontier != []:
            parent = frontier.pop(0)
            children = parent.children
            for child in children:
                frontier.append(child)
                dot_text += "\n\t{c} -> {p};".format(p='<' + str(parent.block) + '>',
                                                     c='<' + str(child.block) + '>'
                                                     )
        dot_text += "\n}"
        with open("blockchain.gv", "w") as writeFile:
            writeFile.write(dot_text)

class BlockNode(object):
    """
    Holds a single block in the Blockchain tree.

    Contains the parent block if one exists and children blocks if they exist.
    Each block must have exactly one parent unless it is the root node. The hash
    of the Block in question is also considered the hash of the BlockNode.
    """

    def __init__(self, block: Block, parent):
        """
        Construct the BlockNode given a Block and the BlockNode of its parent.

        :param block: The Block which this node holds
        :param parent: The parent BlockNode representing the parent Block
        """
        self.parent = parent
        self.block = block
        self.children = []
        self.depth = 1 if parent is None else parent.depth + 1
        self.tree_num = Blockchain.num_trees if parent is None else parent.tree_num
        if self.parent is None:
            self.fork_num = 0
        elif self.parent.block.is_root():
            self.fork_num = Blockchain.fork_counter
            Blockchain.fork_counter += 1
        else:
            self.fork_num = self.parent.fork_num

        if self.fork_num not in Blockchain.fork_lengths:
            Blockchain.fork_lengths[self.fork_num] = self.depth
        elif Blockchain.fork_lengths[self.fork_num] < self.depth:
            Blockchain.fork_lengths[self.fork_num] = self.depth

    def add_child(self, child):
        """Add a child BlockNode"""
        self.children.append(child)

    @property
    def get_time(self):
        """Return the Block's time of creation."""
        return self.block.create_time

    @property
    def get_hash(self):
        return self.block.block_hash

    @property
    def posts(self):
        return self.block.posts
