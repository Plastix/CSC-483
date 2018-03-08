MIN_PEERS = 5
MAX_PEERS = 10
MAX_PEER_FAILURE = 10
UPDATE_PAD = 60
WAIT_TIME = 0.10
TIMEOUT = 1.0

MESSAGE_TYPE = 0
BLOCK_TYPE = 1

DEFAULT_PORT = 50000
MAIN_HOST = "andersm2-macpro.union.edu"  # Test
# MAIN_HOST = "andersm2-vrtower.union.edu"  # Production

MSG_BUFFER_SIZE = 100
MSGS_PER_BLOCK = 10
PROOF_OF_WORK_HARDNESS = 5

# Block spacing constants
NONCE = 0
PARENT_HASH = 1
CREATE_TIME = 3
BLOCK_MINER = 2
MESSAGE_START = 4

# Message spacing constants
SENDER_KEY = 0
MSG_BODY = 1
MSG_SIG = 2

# Message body spacing constants
MSG_TIME = 0
MSG_TEXT = 1
MSG_PUB_KEY = 2

# Key files
PUBLIC_KEY_FILE = 'public_keys.pem'
PRIVATE_KEY_FILE = 'private_keys.pem'
KEY_DIRECTORY = 'key_directory.pem'

LEDGER_FILE = 'ledger.txt'
MESSAGE_FILE = 'messages.txt'
