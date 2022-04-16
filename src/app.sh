#!/usr/bin/env bash
path=$(dirname "$0")
path=$(realpath "$path/../")
export PYTHONPATH="$path:$PYTHONPATH"
export PATH="$path:$PATH"
cd "$path" || ..
gunicorn -c src/web/gunicorn_config.py src.web.app:app
