#!/bin/bash

# usage: ./start_server.sh <username> <port>

cd ../lab_grades/$1/
python3 ../../bin/server.py $1 $2

