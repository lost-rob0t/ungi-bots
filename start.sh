#!/usr/bin/env bash
set -euo pipefail

# usage: ./start.sh tokens.txt
# i was retarted when i made this so to stop pkill -f discord_logger.py
tokens=$1

# This a discord hard limit, each channel can have no more
# than 2000 messages.
max_history=2000

while read token; do
    python discord_logger.py -t $token -m $max_history &
done < $tokens
