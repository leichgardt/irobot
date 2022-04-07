#!/bin/bash
if [ "$1" = "web" ]; then
  /bin/bash src/app.sh
else
  /bin/bash src/bot.sh
fi