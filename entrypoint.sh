#!/bin/bash
if [ ! -f ./src/config_params.txt ]; then
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
      echo "$url" > src/config_params.txt
      echo "$login" >> src/config_params.txt
      echo "$pwd" >> src/config_params.txt
      flag=false
      break
    fi
  done
fi
if [ "$1" = "web" ]; then
  gunicorn -c src/guni.py src.app:app
else
  python src/run_bot.py
fi