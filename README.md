# irobot
Проект состоит из двух частей: 
1) Телеграм-бот;
2) Веб-приложение.

С помощью бота можно проверять баланс, пополнять счет, получать уведомления и общаться с поддержкой.

С помощью веб-приложения происходит авторизация в боте (через HTTPS). Также присутствует веб-интерфейс для операторов,
предназначенный для выполнения рассылки уведомлений и новостей и для оказания технической поддержки через чат.

## Взаимодействие
* `LanBilling` - система биллинга интернет провайдеров
* `Userside` - ERP система для организации и упрощения работ с системами биллинга, логистикой, учётом и т.д.

## Требования
* python 3.8
* docker
* postgresql
* mongodb
* nginx или apache

## Установка
### 1. Файл конфигурации config.py
Перед сборкой отредактируйте конфигурационный файл `config.py`. Следует указать все параметры для корректной работы 
системы (параметры бизнес-процессов можно пропустить).

### 2. Dockerfile
После собираем образ из директории проекта вместе с `Dockerfile` с помощью команды
```shell
docker build -t irobot -f Dockerfile .
```
где t - название для образа.

## Запуск
### Первый запуск и Тест
В первый запуск создадим необходимые таблицы в БД и протестируем с помощью команды:
```shell
docker run -it --rm irobot test
```

### Разработка
Чтобы создать <u>контейнер с ботом</u> выполните:
```shell
docker run -it -p 5421:5421 --name irobot irobot bot
```

Для отсоединения от контейнера нажмите последовательно `Ctrl+p Ctrl+q` (или `Ctrl+p+q`).

Чтобы создать <u>контейнер с веб-приложением</u> выполните
```shell
docker run -it -p 8000:8000 --name irobot-web irobot web
```

Вы можете зайти внутрь запущенного контейнера, чтобы отредактировать файлы, запустить сервисы локально, прочитать логи и т.д.: 
```shell
docker exec -it -u 0 irobot-web /bin/bash
```

> Будьте осторожны! После удаления контейнера, все созданные файлы внутри контейнера будут потеряны! 
> Но это не относится к остановке контейнера.

### Продакшн
Снова создаем те же два контейнера, но добавляем флаги `restart=always` `volume`
```shell
$ docker run -p 5421:5421 --restart=always --name irobot irobot bot
$ docker run -p 8000:8000 --restart=always --name irobot-web irobot web
```

Также, если вы хотите развернуть контейнеры по-другому, вместо флага `--restart=always`,
контейнеры можно настроить как [systemd сервисы](https://docs.docker.com/config/daemon/systemd/).

## Развёртка
### 1. Настройка перед выпуском
Добавьте параметр в `/etc/sysctl.conf`, чтобы избежать проблем при запуске большого количества веб-сервисов:
> net.core.somaxconn=65535

### 2. Брандмауэр
Если вы используете `iptables` или `ufw` - не забудьте открыть порты.

### 3. Nginx
В файле конфигурации сервера `/etc/nginx/sites-enabled/myserver` добавьте upstream:
```nginx
upstream irobot {
    server 127.0.0.1:8000;
}

upstream irobot_webhook {
    server 127.0.0.1:5421;
}
```
А в блок `server` следующее:
```nginx
location /irobot/ {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Script-name /irobot/;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://irobot/;
    proxy_buffering off;
    proxy_redirect off;
}

location /irobot_webhook/ {
    proxy_set_header X-Script-Name /irobot_webhook/;
    proxy_set_header Host $host;
    proxy_pass http://irobot_webhook/;
    proxy_redirect off;
}
```
Далее тестируем и обновляем настройки:
```shell
$ nginx -t
$ nginx -s reload
```

> Если вы будете разворачивать приложение без субдиректории (без `location /irobot/`), 
> то вам будет необходимо установить параметр прокси в None - `ROOT_PATH=None` - в файле конфигурации `config.py`.

## Администрирование
Для администрирования зайдите на страницу `https://{your-domain}/irobot/admin/` 
(или `http://127.0.0.1:8000/irobot/admin/` при отладке), используя логин/пароль `admin`/`123456`.

> Учтите! Панель администрирования доступна только из под локальной сети! Для добавления исключения добавьте 
> необходимый IP в параметр `HOST_IP_LIST` в файле `config.py`