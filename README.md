# irobot
Телеграм бот для интернет-провайдера

## requirements
### libs
* python3.8
* python3-venv
* python3-pip

### configuration
Добавьте параметр в `/etc/sysctl.conf` для корректной работы сервера:
> net.core.somaxconn=65535

## installing
Для установки среды и пакетов запустите `setup.sh` после установки библиотек.

## running
> gunicorn -k main.IrobotWebUvicornWorker -c guni.py app:app
