This directory contains the experimental grade access system for CSC 483.

Directory structure:

README.txt             : This file

users.txt              : Contains first names, usernames, passwords, port numbers for all users

bin/                   : Scripts for starting servers and underlying python code

    start_server.sh    : Starts a server for given student on a port, always running for each student
                         usage  ./start_server.sh <username> <port>

    server.py          : Simple python server run by start_server.sh
    
    start_final_server : Starts final grade server only runs when I need to examine final grades.
    		         usage  ./start_final_server <port>

    final_server.py    : Simple python server run by start_final_server.  A minor modification to server.py
    

final_grades/          : Stores final grade files for all students, only
                         accessible as root for security reasons.


lab_grades/<user>/     : stores lab grades for all students, will contain student work eventually.


TODO:

 - Find and fix security flaws?
