# crack.py
# A very inefficient password cracker
#
# Aidan Pieper
# CSC 483
# Winter 2018

from enum import Enum
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from binascii import hexlify, unhexlify
import sys
import time
import itertools


class Mode(Enum):
    BRUTE_FORCE = 1
    DICTIONARY_ATTACK = 2
    PRIOR_KNOWLEDGE = 3


# noinspection PyShadowingNames
def compute_hash(password, salt):
    hash = pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hexlify(hash).decode()


# noinspection PyShadowingBuiltins,PyShadowingNames
def compare_pass(word, hash, salt):
    word_hash = compute_hash(word, salt)
    return compare_digest(hash, word_hash)


# noinspection PyShadowingNames,PyShadowingBuiltins
def break_password(mode, hash, salt, regex):
    print(mode)
    print('Hash: {0} Salt: {1} Regex: {2}'.format(hash, salt, regex))
    num = 0
    password = None
    start_time = time.time()
    if mode == Mode.BRUTE_FORCE:
        # Init with all 1 character passwords
        strings = [chr(x) for x in range(32, 127)]
        found = False
        while not found:
            for word in strings:  # Search accrued list of words
                if compare_pass(word, hash, salt):
                    password = word
                    found = True
                    break
                num += 1
                # Add all possible suffixes to current string to end of list
                strings.extend((word + chr(x) for x in range(32, 127)))

    elif mode == Mode.DICTIONARY_ATTACK:
        with open('/usr/share/dict/words', 'r') as dictionary:
            for raw_word in dictionary:
                word = raw_word.strip()
                if compare_pass(word, hash, salt):
                    password = word
                    break
                num += 1

    elif mode == Mode.PRIOR_KNOWLEDGE:
        stars = regex.count('*')
        chars = (chr(x) for x in range(32, 127))
        perms = itertools.product(chars, repeat=stars)  # Calculate all perms of stars length
        for perm in perms:
            j = 0
            word = list(regex)
            for i, x in enumerate(word):
                if x == '*':
                    word[i] = perm[j]
                    j += 1
            if compare_pass(''.join(word), hash, salt):
                password = word
                break
            num += 1

    else:
        raise RuntimeError('Undefined mode {}!'.format(mode))

    elapsed = round(time.time() - start_time, 2)
    if password is None:
        print('\nPassword not found!\nTime: {0}s\nPasswords checked: {1}'.format(elapsed, num))
    else:
        print('\nPassword: \'{0}\'\nTime: {1}s\nPasswords checked: {2}'.format(password, elapsed, num))


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 2:
        print('usage: python3 {} <file name>'.format(args[0]))
        exit(1)

    try:
        with open(args[1], 'r') as cfile:
            mode = Mode(int(cfile.readline().strip()))
            regex = cfile.readline().strip()
            salt = unhexlify(cfile.readline().strip())
            hash = cfile.readline().strip()

            break_password(mode, hash, salt, regex)
    except IOError:
        print("Error reading password configuration file!")
        exit(1)
