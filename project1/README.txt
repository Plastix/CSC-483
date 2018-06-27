Project 1 - Securing the Insecure
This directory contains the experimental grade access system for CSC 483.

Fixed security issues:

Unencrypted communication
=========================
Usernames and passwords are no longer sent to the server unencrypted. We now use SSL sockets for sending this private data.
We load our (self-signed) SSL certificates and wrap the normal communication socket with a SSL socket before reading and
writing data.

Plain-text password storage
===========================
Passwords are now salted and hashed before storing in the users.txt file. This means that an attacker can no longer directly
read off this information if given the file. We use the PKCS function with a hash digest algorithm of SHA-256 with
100,000 iterations. Salts are 32 bytes long and are randomly generated using Python's os.urandom() function. The users.txt
file stores each user account on a single line in the format <username> <password hash> <salt>. New users can be added to
the system by adding a new line to the users.txt file with only a username. The next boot of the server will automatically
set a default password for the new user which is their username.

Shell injection
===============
Arbitrary shell code is no longer able to be executed through the username input. Instead of printing the grades file using
cat we open the file and print it via Python. If the user has no grades file, i.e. andersm2, an error message is printed
to the console instead of a stacktrace.


Privilege Escalation
====================
Final grade server and files have been removed from the repository (Nexus instructions say to disregard these files).
Final grades should probably be isolated from lab grades.


Security Principles:
This version of the grade system is slightly more secure than the original but it does not provide good security. The
server code is still pretty small (~150 lines) so it obeys the Economy of design security principle. The system does not
do well with Separation of privilege since users are only required to enter a single password to access the system. Moreover,
users can only change their password once after logging in the first time with a default password. In a sense the system now
has Layered defenses since communication is encrypted and the password "database" is hashed and salted.


Directory structure:

README.txt             : This file

users.txt              : Contains usernames, (hashed) passwords, and salts for all users

bin/                   : Scripts for starting servers and underlying python code

    start_server.sh    : Starts a server for given student on a port, always running for each student
                         usage  ./start_server.sh <username> <port>

    server.py          : Simple python server run by start_server.sh

lab_grades/<user>/     : stores lab grades for all students, will contain student work eventually.


