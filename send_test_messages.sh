#!/bin/bash
for run in {1..10}
do
  echo "Sending message $run"
  python3 send_message.py TEST_MESSAGE_PLEASE_IGNORE 0
done