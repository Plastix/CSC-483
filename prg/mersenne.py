# mersenne.py
# A poorly implemented PRG
#
# Aidan Pieper
# CSC 483
# Winter 2018

class Mersenne:

    def __init__(self):
        self.N = 624
        self.M = 397
        self.A = 0x9908b0df
        self.UPPER = 0x80000000
        self.LOWER = 0x7fffffff
        self.m = [0] * self.N
        self.mi = self.N

    def setSeed(self, seed):
        self.m[0] = seed & 0xffffff
        i = 1
        while i < len(self.m):
            self.m[i] = (69069 * self.m[i - 1]) & 0xffffffff
            i += 1
        self.mi = self.N

    def nextInt(self):
        if self.mi >= self.N:
            k = 0
            while k <= self.N - 1:
                y = (self.m[k] & self.UPPER) | (self.m[(k + 1) % self.N] & self.LOWER)
                self.m[k] = self.m[(k + self.M) % self.N] ^ (y >> 1)
                if y % 2 == 1:
                    self.m[k] = self.m[k] ^ self.A
                k += 1
            self.mi = 0
        y = self.m[self.mi]
        self.mi += 1
        y = y ^ (y >> 11)
        y = y ^ ((y << 7) & 0x9d2c5680)
        y = y ^ ((y << 15) & 0xefc60000)
        y = y ^ (y >> 18)
        return y
