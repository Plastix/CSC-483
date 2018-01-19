# crack.py
# Aidan Pieper
# CSC 483
# Winter 2018

from enum import Enum
from hashlib import pbkdf2_hmac
from binascii import hexlify
import sys


class Mode(Enum):
    BRUTE_FORCE = 1
    DICTIONARY_ATTACK = 2
    PRIOR_KNOWLEDGE = 3


def compute_hash(password, salt):
    hash = pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hexlify(hash).decode()


def break_password(mode, hash, salt, regex):
    pass


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print('usage: python3 {} <file name>'.format(args[0]))
        exit(1)

    try:
        with open(args[1], 'r') as cfile:
            mode = Mode(cfile.readline())
            regex = cfile.readline()
            salt = cfile.readline()
            hash = cfile.readline()

            break_password(mode, hash, salt, regex)
    except IOError:
        print("Error reading password configuration file!")
        exit(1)
