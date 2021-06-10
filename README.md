# irobot
Проект состоит из двух частей: 
1) Телеграм-бот;
2) Веб-приложение.

С помощью бота можно проверять баланс, пополнять счет через YooMoney.

С помощью веб-приложения можно отправлять рассылки и уведомления пользователям бота, просматривать отправленные сообщения и многое другое.

## Требования
### Библиотеки
* python3.8
* python3-venv
* python3-pip
* systemd
* nginx

## Установка
Для установки среды и пакетов запустите `setup.sh` после установки библиотек.

## Старт
### Development
Для теста ASGI приложения запустите `app.py` 
> (venv) $ python app.py
### Production
#### Запуск
Для запуска в продакшн используется веб-сервер gunicorn.
> (venv) $ gunicorn -c guni.py app:app

######Обратите внимание, что в файле конфигурации `guni.py` указан пользователь `www-data` для запуска из под `systemd` для `nginx`.
#### Настройка
Добавьте параметр в `/etc/sysctl.conf` для корректной работы сервера:
> net.core.somaxconn=65535

## Развёртка
### systemd
Расположите файл unix-сервиса `irobot.service` в директории `/etc/systemd/system/`, и заполните его следующим:
```
[Unit]
Description=IroBot Web
Wants=nginx.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/irobot
Environment="PATH=/var/www/irobot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/var/www/irobot/venv/bin/gunicorn -c guni.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
Restart=always

[Install]
WantedBy=multi-user.target
```
Далее введите следующие команды
> $ systemctl daemon-reload
> 
> $ systemctl enable --now irobot
> 
> $ service irobot status

### nginx
В вашем файле конфигурации сервера `/etc/nginx/sites-enabled/myserver` добавьте upstream:
```
upstream irobot {
    server 127.0.0.1:8000;
}
```
И следующее в блок `server`:
```
location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Script-name /fast;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://irobot/;
}
```
Далее, протестировав настройки, обновите их:
> $ nginx -t
> 
> $ nginx -s reload

