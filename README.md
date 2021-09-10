# irobot
Проект состоит из двух частей: 
1) Телеграм-бот;
2) Веб-приложение.

С помощью бота можно проверять баланс, пополнять счет через YooMoney и получать уведомления.

Веб-приложение представлено для веб-авторизации пользователей в боте, а так же для новостной и уведомительной рассылки 
и многое другое.

## Требования
* docker (https://docs.docker.com/get-docker/)
* nginx или apache или подобное (для развёртывания)
* mongodb (опционально - проект уже подключается к существующей БД)

## Установка проекта
В директории проекта необходимо собрать образ с помощью файла `Dockerfile` командой
```shell
$ docker build -t irobot -f Dockerfile .
```

Для установки среды разработки потребуется:
* python3.8 python3-pip python3.8-venv
* git

Создайте виртуальную среду и установите зависимости
```shell
python3.8 -m venv venv
sourve venv/bin/activate
pip install -U pip setuptools wheel
pip install -r requirements.txt
mkdir -p installations/emoji
git clone https://github.com/carpedm20/emoji.git installations/emoji 
cd installations/emoji
python setup.py install
cd ../..
rm -rf installations
```

## Запуск
### Development
Для теста приложений без контейнера запустите `app.py` или `run_bot.py`
```shell
$ source venv/bin/activate
(venv) $ python src/app.py
(venv) $ python src/run_bot.py
```

В файле конфигурации gunicorn-сервера `src/guni.py` указан пользователь `www-data`. Можете закомментировать строки для
тестирования из-под своего пользователя 

### Production
Для запуска приложений на основе образа `irobot` необходимо создать два контейнера: с ботом и с веб-приложением
```shell
$ docker run -it -p 5421:5421 --restart=always --name irobot irobot bot
$ docker run -it -p 8000:8000 --restart=always --name irobot-web irobot web
```
Во время создания контейнеров будет запрошена информация для доступа к файлу конфигурации: url, login, password.
Получить их можно на Локальной Wiki: 
> Ironnet Wiki >> Сервера >> CUP (ЦУП) >> "Главный файл конфигурации".

### Настройка
Добавьте параметр в `/etc/sysctl.conf`, чтобы избежать проблем при запуске большого количества сервисов:
> net.core.somaxconn=65535

## Развёртка
### nginx
В вашем файле конфигурации сервера `/etc/nginx/sites-enabled/myserver` добавьте upstream:
```nginx
upstream irobot {
    server 127.0.0.1:8000;
}

upstream irobot_webhook {
    server 127.0.0.1:5421;
}
```
И следующее в блок `server`:
```nginx
location /irobot {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Script-name /fast;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://irobot/;
    proxy_buffering off;
    proxy_redirect off;    
}

location /irobot_webhook {
    proxy_set_header X-Script-Name /irobot_webhook;
    proxy_set_header Host $host;
    proxy_pass http://irobot_webhook/;
    proxy_redirect off;
}
```
Далее, протестировав настройки, обновите их:
```shell
$ nginx -t
$ nginx -s reload
```
