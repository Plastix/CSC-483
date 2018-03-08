import hashlib
import threading
from blockchain import *
from network import *
from blockchain_constants import *

from time import sleep


def main():
    blockchain = Blockchain(LEDGER_FILE)
    blockchain_thread = threading.Thread(target=blockchain.mine)
    # blockchain_thread.daemon = True
    blockchain_thread.start()

    server = Server(blockchain, True, True, True)
    server.run()
    # Main thread is server thread
    # This call never returns


main()
