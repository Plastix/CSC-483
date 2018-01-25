from cipher import FastStreamCipher
from random import randint
from time import time

if __name__ == '__main__':
    secret = randint(2 ** 15, 2 ** 50)
    cipher = FastStreamCipher(randint(2 ** 15, 2 ** 50))

    # text = 'This is a demo of a simple cipher.'
    text = "Demo of cipher!"
    print("Message: ", text)

    cipher_text = cipher.encrypt(secret, text)
    print("Encrypt function: ", cipher_text)

    decrypted = cipher.decrypt(secret, cipher_text)
    print("Decrypt function: ", decrypted)

    print("Eavesdrop function:")
    start = time()
    brute_forced = cipher.eavesdrop(cipher_text)
    if brute_forced is not None:
        print("Brute forced ciphertext!", brute_forced)
    else:
        print("Could not brute force ciphertext!")

    print("Time:", round(time() - start, 2), "s")
