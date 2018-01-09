# Simple and completely insecure grade-accessing server.
# Author: Matt Anderson
# Version: Winter 2018

import sys
from socket import *
import subprocess

# Check arguments
args = sys.argv
if len(args) != 2:
    print("Usage: python3 server.py <port-number>")
    exit()
    

# Read usernames and passwords from file.
passwords = {}

try:
    pw_file = open('../users.txt','r')
except:
    print("Error: Unable to locate users.txt")
    exit()
    
lines = pw_file.readlines()
#<firstname> <username> <password> <port>
for line in lines:
    toks = line.strip().split()
    passwords[toks[1]] = toks[2]

# Configure socket parameters.
try:
    port = int(args[1])
except:
    print("Error: Invalid port number")
    exit()
    
host = ''
addr = (host, port)
buf_len = 4096

# Create TCP socket to listen on.
try:
    sock = socket(AF_INET,SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(1)
    print("Server started up on port", port)
except:
    print("Error: Unable to start sever on port", port)
    exit()


# Loop waiting for connections
while True:

    # Wait for a new connection
    connection, client_address = sock.accept()

    print('Accepted connection from', client_address)
    
    f_in = connection.makefile('r')
    f_out = connection.makefile('w')

    # Request password.
    f_out.write("Please enter andersm2's password: ")
    f_out.flush()
    pw = f_in.readline().strip()


    # Request username.
    f_out.write("Please enter username to look up: ")
    f_out.flush()
    uname = f_in.readline().strip()

    # Clean up username
    if len(uname) < 8:
        clean_uname = ""
    else:
        clean_uname = uname[0:8]
    

    try:

        # Check for valid user/password pair.
        if passwords["andersm2"] != pw:
            f_out.write("Error: Invalid username or password combination.\n")
            f_out.flush()

        else:
            # Cat the student grade file in the directory back to client.
            # WARNING: This is a terrible way to pass on the contents of a single file.
            #          Never write code like this!!!
            proc = subprocess.Popen(["cat ../final_grades/final_%s" % uname], stdout=f_out,stdin=f_in, \
                                    stderr=subprocess.STDOUT,shell=True)
            
            # Wait for the process to complete.
            proc.wait()

    # Terminate connection and clean up
    finally:
        connection.close()
        f_in.close()
        f_out.close()
        print("Closed connection from", client_address)


