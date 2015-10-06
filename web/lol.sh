#!/bin/bash

cd "$(dirname "$0")"

. ../venv/bin/activate
python ../web.py
