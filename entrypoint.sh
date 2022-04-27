#!/bin/bash

path=$(dirname "$0")
path=$(realpath "$path/../")

export PYTHONPATH="$path:$PYTHONPATH"
export PATH="$path:$PATH"

if [ "$1" = "web" ]; then
  gunicorn -c src/web/gunicorn_config.py src.web.app:app

elif [ "$1" = "bot" ]; then
  python src/bot/run_bot.py

elif [ "$1" = "test" ]; then
  python src/modules/sql/checker.py
  pytest tests

else
  /bin/bash

fi