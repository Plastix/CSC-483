# cipher.py
# A basic symmetric key cipher using mersenne.py
#
# Aidan Pieper
# CSC 483
# Winter 2018
#
# Honor code:
# James and I worked together to figure out how to generate the correct number of bytes
#
from mersenne import Mersenne, FastMersenne


class StreamCipher:

    def __init__(self, init_vector) -> None:
        super().__init__()
        self.init = init_vector
        self.prg = Mersenne()

    def __xor_text(self, secret, text):
        self.prg.set_seed(secret ^ self.init)

        num_bytes = len(text)

        # Generate exactly enough bytes to xor with our text
        rand = b''
        while len(rand) < num_bytes:
            n = self.prg.next_int()
            rand += self.__int_to_byte(n)
        rand = rand[:num_bytes]

        cipher = b''
        for a, b in zip(text, rand):
            xor = a ^ b
            cipher += self.__int_to_byte(xor)

        return cipher

    def __int_to_byte(self, n):
        return n.to_bytes((n.bit_length() + 7) // 8, 'big')

    def encrypt(self, secret, plaintext):
        return self.__xor_text(secret, plaintext.encode('ascii'))

    def decrypt(self, secret, ciphertext):
        return self.__xor_text(secret, ciphertext).decode('ascii')


class FastStreamCipher(StreamCipher):
    def __init__(self, init_vector) -> None:
        super().__init__(init_vector)
        self.prg = FastMersenne()

    def eavesdrop(self, ciphertext):
        secret = 0
        while secret <= 0xffffff:
            try:
                decrypt = self.decrypt(secret, ciphertext)
                return decrypt
            except UnicodeDecodeError:
                pass
            secret += 1
        else:
            return None
