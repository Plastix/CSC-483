import hashlib
import threading
from blockchain import *
from network import *
from blockchain_constants import *

from time import sleep


def main():
    
    blockchain = Blockchain()
    blockchain_thread = threading.Thread(target=blockchain.mine)
    blockchain_thread.daemon = True
    blockchain_thread.start()
    
    server = Server(blockchain, True, True, True)
    server_thread = threading.Thread(target=server.run)
    server_thread.daemon = True
    server_thread.start()
    # Main thread is server thread
    # This call never returns
    sleep(30)
    print(blockchain.get_all_block_strs(0))


main()