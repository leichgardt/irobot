#!/bin/bash
path=$(dirname "$0")
rootpath=$(realpath "$path/../")
export PYTHONPATH="$rootpath:$PYTHONPATH"
python "$path"/bot/run_bot.py
