#!/bin/bash
config_file=./src/utils/config_params.txt
if [ ! -f $config_file ]; then
  flag=true
  while $flag
  do
    echo -n "Enter URL for config file: "
    read -r url
    if [ "${url}" = "" ]; then
      echo "URL is empty!"
      continue
    fi
    echo -n "Enter login: "
    read -r login
    if [ "${login}" = "" ]; then
      echo "Login is empty!"
      continue
    fi
    echo -n "Enter password: "
    read -rs pwd
    if [ "${pwd}" = "" ]; then
      echo "Password is empty!"
      continue
    fi
    echo ""
    echo -n "Confirm this data input? (Y/n): "
    read -r res
    if [ "${res}" = "" ] || [ "${res}" = "y" ] || [ "${res}" = "Y" ]; then
      echo "$url" > $config_file
      echo "$login" >> $config_file
      echo "$pwd" >> $config_file
      flag=false
      break
    fi
  done
fi
if [ "$1" = "web" ]; then
  /bin/bash src/app.sh
else
  /bin/bash src/bot.sh
fi