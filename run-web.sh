#!/bin/bash

cd "$(dirname "$0")"

pkill -f /bots/venv/bin/python server.py

screen -S server -d -m sh web/lol.sh 
screen -r server
