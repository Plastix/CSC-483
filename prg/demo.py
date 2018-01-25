from cipher import StreamCipher
from random import randint
from time import time

if __name__ == '__main__':
    secret = randint(2 ** 15, 2 ** 50)
    cipher = StreamCipher(randint(2 ** 15, 2 ** 50))

    # text = 'This is a demo of a simple cipher.'
    text = "Demo of cipher!"
    print("Message: ", text)

    cipher_text = cipher.encrypt(secret, text)
    print("Encrypt function: ", cipher_text)

    decrypted = cipher.decrypt(secret, cipher_text)
    print("Decrypt function: ", decrypted)

    print("Eavesdrop function:")
    start = time()
    cipher.eavesdrop(cipher_text)
    print(time()-start)
