Project 1 - Securing the Insecure
This directory contains the experimental grade access system for CSC 483.

Fixed security issues:

Unencrypted communication
=========================
Usernames and passwords are no longer sent to the server unencrypted. We now use SSL sockets for sending this private data.
We load our (self-signed) SSL certificates and wrap the normal communication socket with a SSL socket before reading and
writing data

Plain-text password storage
===========================
Passwords are now salted and hashed before storing in the users.txt file. This means that an attacker can no longer directly
read off this information if given the file. We use the PKCS function with a hash digest algorithm of SHA-256 with
100,000 iterations. Salts are 32 bytes long and are randomly generated using Python's os.urandom() function. The users.txt
file stores each user account on a single line in the format <username> <password hash> <salt>.

Shell injection
===============
Arbitrary shell code is no longer able to be executed through the username input. Instead of printing the grades file using
cat we open the file and print it via Python.


Privilege Escalation
====================
Final grade server and files have been removed from the repository (Nexus instructions say to disregard these files).
Final grades should probably be isolated from lab grades.


Directory structure:

README.txt             : This file

users.txt              : Contains usernames, (hashed) passwords, and salts for all users

bin/                   : Scripts for starting servers and underlying python code

    start_server.sh    : Starts a server for given student on a port, always running for each student
                         usage  ./start_server.sh <username> <port>

    server.py          : Simple python server run by start_server.sh

lab_grades/<user>/     : stores lab grades for all students, will contain student work eventually.


