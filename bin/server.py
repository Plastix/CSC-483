# Simple and (slightly) more secure grade-accessing server.
# Author: Matt Anderson
# Version: Winter 2018
# Aidan Pieper

import sys
from socket import *
import ssl
import hashlib
import hmac
import os
import binascii


def hash_password(password, salt):
    raw_hash = hashlib.pbkdf2_hmac('sha256', bytes(password, 'UTF-8'), bytes(salt, 'UTF-8'), 100000)
    return str(binascii.hexlify(raw_hash))


# TODO (Aidan) This should be in a try catch
def save_user_file(lines):
    with open('../../users.txt', 'w') as pw_file:
        pw_file.writelines(lines)


def read_user_file():
    try:
        pw_file = open('../../users.txt', 'r')
    except:
        print('Error: Unable to locate users.txt')
        exit()

    pswds = {}
    lns = list(pw_file.readlines())
    rewrite = False
    # <username> <password hash> <salt>
    for index, line in enumerate(lns):
        tokens = line.strip().split(maxsplit=3)

        # New users just have a username in the text file
        # We need to set a default password and salt
        if len(tokens) == 1:
            username = tokens[0]
            salt = str(os.urandom(32))
            digest = hash_password(username, salt)
            lns[index] = '{0} {1} {2}\n'.format(username, digest, salt)
            rewrite = True

        else:
            username = tokens[0]
            digest = tokens[1]
            salt = tokens[2]

        pswds[username] = (digest, salt, index)

    if rewrite:
        save_user_file(lns)

    return lns, pswds


# Check arguments
args = sys.argv
if len(args) != 3:
    print('Usage: python3 server.py <username> <port-number>')
    exit()

# Read usernames and passwords from file.
lines, passwords = read_user_file()

# Configure socket parameters.
try:
    port = int(args[2])
except:
    print('Error: Invalid port number')
    exit()

host = ''
addr = (host, port)

# Create TCP socket to listen on.
try:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(1)
    print('Started server, pid: %d, user: %s, port: %d' % (os.getpid(), args[1], port))
except:
    print('Error: Unable to start sever on port', port)
    exit()

# Set up SSL
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile='../../certs/certificate.pem', keyfile='../../certs/key.pem')

# Loop waiting for connections
while True:

    # Wait for a new connection
    connection, client_address = sock.accept()

    ssl_connection = context.wrap_socket(connection, server_side=True)

    print('Accepted connection from', client_address)

    f_in = ssl_connection.makefile('r')
    f_out = ssl_connection.makefile('w')

    # Request username.
    f_out.write('Please enter username: ')
    f_out.flush()
    uname = f_in.readline().strip()

    # Clean up username
    if len(uname) < 8:
        clean_uname = ""
    else:
        clean_uname = uname[0:8]

    # Request password.
    f_out.write('Please enter password: ')
    f_out.flush()
    pw = f_in.readline().strip()

    try:
        # Check for valid user/password pair.
        if clean_uname not in passwords.keys() or not hmac.compare_digest(passwords[clean_uname][0],
                                                                          hash_password(pw, passwords[clean_uname][1])):
            f_out.write('Error: Invalid username or password combination.\n')
        else:
            try:
                with open('grades_{0}'.format(clean_uname), 'r') as grades:
                    f_out.write(grades.read())
            except:
                f_out.write('No grades available for {0}!\n'.format(clean_uname))

            # User has a default password which they need to change
            if hmac.compare_digest(passwords[clean_uname][0], hash_password(clean_uname, passwords[clean_uname][1])):
                f_out.write('You must change your default password. Please enter a new password: ')
                f_out.flush()
                pw = f_in.readline().strip()
                salt = str(os.urandom(32))
                digest = hash_password(pw, salt)
                lines[passwords[clean_uname][2]] = '{0} {1} {2}\n'.format(clean_uname, digest, salt)
                save_user_file(lines)
                lines, passwords = read_user_file()

        f_out.flush()


    # Terminate connection and clean up
    finally:
        connection.close()
        ssl_connection.close()
        f_in.close()
        f_out.close()
        print('Closed connection from', client_address)
