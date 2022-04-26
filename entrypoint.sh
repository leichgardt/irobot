#!/bin/bash
if [ "$1" = "web" ]; then
  /bin/bash src/app.sh
elif [ "$1" = "bot" ]; then
  /bin/bash src/bot.sh
elif [ "$1" = "test" ]; then
  python src/modules/sql/checker.py
  pytest tests
else
  /bin/bash
fi