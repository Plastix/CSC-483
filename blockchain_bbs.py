import hashlib
import threading
import os
from blockchain import *
from network import *
from blockchain_constants import *

from time import sleep

def ensure_keys():
    """
    Ensures that our public and private keys exist in the folder.

    :return: None
    """
    if not os.path.exists(PRIVATE_KEY_FILE):
        import generate_user_key


def main(threads):
    ensure_keys()
    blockchain = Blockchain(LEDGER_FILE, MESSAGE_FILE, STATS_FILE)
    bchain_threads = []
    for i in range(threads):
        bchain_threads.append(threading.Thread(target=blockchain.mine))
    # blockchain_thread.daemon = True
    for thread in bchain_threads:
        thread.start()

    server = Server(blockchain, True, True, False)
    server.run()
    # Main thread is server thread
    # This call never returns


if __name__ == "__main__":
    import sys
    threads = 1
    if len(sys.argv) > 1:
        threads = int(sys.argv[1])
    main(threads)
