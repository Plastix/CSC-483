from cipher import StreamCipher

if __name__ == '__main__':
    secret = 99222399
    cipher = StreamCipher(10023)

    text = 'Hello there! This is a demo of a simple cipher.'
    print("Message: ", text)

    cipher_text = cipher.encrypt(secret, text)
    print("Cipher text: ", cipher_text)

    decrypted = cipher.decrypt(secret, cipher_text)
    print("Decrypted plaintext: ", decrypted)
