#!/bin/bash
if [ "$1" = "web" ]; then
  /bin/bash src/app.sh
elif [ "$1" = "bot" ]; then
  /bin/bash src/bot.sh
else
  /bin/bash
fi