# Simple and (slightly) more secure grade-accessing server.
# Author: Matt Anderson
# Version: Winter 2018
# Aidan Pieper

import sys
from socket import *
import ssl

# Check arguments
args = sys.argv
if len(args) != 3:
    print("Usage: python3 server.py <username> <port-number>")
    exit()

# Read usernames and passwords from file.
passwords = {}

try:
    pw_file = open('../../users.txt', 'r')
except:
    print("Error: Unable to locate users.txt")
    exit()

lines = pw_file.readlines()
# <firstname> <username> <password> <port>
for line in lines:
    toks = line.strip().split()
    passwords[toks[1]] = toks[2]

# Configure socket parameters.
try:
    port = int(args[2])
except:
    print("Error: Invalid port number")
    exit()

host = ''
addr = (host, port)

# Create TCP socket to listen on.
try:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(1)
    print("Started server, pid: %d, user: %s, port: %d" % (os.getpid(), args[1], port))
except:
    print("Error: Unable to start sever on port", port)
    exit()

# Set up SSL
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="../../certs/certificate.pem", keyfile="../../certs/key.pem")

# Loop waiting for connections
while True:

    # Wait for a new connection
    connection, client_address = sock.accept()

    ssl_connection = context.wrap_socket(connection, server_side=True)

    print('Accepted connection from', client_address)

    f_in = ssl_connection.makefile('r')
    f_out = ssl_connection.makefile('w')

    # Request username.
    f_out.write("Please enter username: ")
    f_out.flush()
    uname = f_in.readline().strip()

    # Clean up username
    if len(uname) < 8:
        clean_uname = ""
    else:
        clean_uname = uname[0:8]

    # Request password.
    f_out.write("Please enter password: ")
    f_out.flush()
    pw = f_in.readline().strip()

    try:

        # Check for valid user/password pair.
        if not clean_uname in passwords.keys() or passwords[clean_uname] != pw:
            f_out.write("Error: Invalid username or password combination.\n")
            f_out.flush()

        else:
            with open("grades_{0}".format(clean_uname), "r") as grades:
                f_out.write(grades.read())
                f_out.flush()

    # Terminate connection and clean up
    finally:
        connection.close()
        ssl_connection.close()
        f_in.close()
        f_out.close()
        print("Closed connection from", client_address)
