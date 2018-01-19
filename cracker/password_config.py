# password_config.py
# Aidan Pieper
# CSC 483
# Winter 2018
#
# Used for generating input files to crack.py


import hashlib
import binascii
import os
import sys

if __name__ == '__main__':
    args = sys.argv

    if len(args) != 4:
        print('usage: python3 {} <mode #> <password> <regex>'.format(args[0]))
        exit(1)

    try:
        with open("test_pass.txt", "w") as f:

            mode = int(args[1])
            password = args[2]
            regex = args[3]
            salt = os.urandom(16)
            hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)

            f.write("{}\n".format(mode))
            f.write("{}\n".format(regex))
            f.write(binascii.hexlify(salt).decode() + "\n")
            f.write(binascii.hexlify(hash).decode() + "\n")
    except (IOError, ValueError) as e:
        print("Error reading input or writing file!")
