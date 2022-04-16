VERSION = '1.1.1'
ABOUT = """Веб-приложение IroBot-web предназначено для рассылки новостей и уведомлений пользователям бота @{}, 
а так же для обработки запросов платежей от системы Yoomoney.\n
"""

# Режим отладки:
# 1) MemoryStorage для бота вместо MongoStorage
# 2) Бот при запуске сбрасывает пропущенные запросы (skip updates)
# 3) Веб-приложение игнорирует root_path для запуска без модификаторов URL
# 4) Сервер веб-приложения Gunicorn отключает параметр пользователя "www-data"
# 5) Веб-приложение не использует большую часть мониторов (SoloWorker)
# 6) Веб-приложение переключается на тестовую таблицу PID
DEBUG = False

# Bot port
BOT_PORT = 5421

# Telegram Bot Token
BOT_TOKEN = '<telegram token>'

# Telegram Bot Payments 2.0 Token
BOT_PAYMENT_TOKEN = '<telegram payment token>'
# E-mail для чеков
RECEIPT_EMAIL = 'admin@bot.ru'

# ID телеграм чата для тестирования, мониторинга статуса бота
TELEGRAM_TEST_CHAT_ID = 1234567890

# IP for connecting to websocket
WEB_SERVICE_IP = '127.0.0.1'
# Port of web app
WEB_SERVICE_PORT = 8000

# root proxy path
ROOT_PATH = '/irobot'

# URL главной веб-страницы
HOST_URL = 'https://my.bot.ru/'

# URL вебхука бота для Телеграм API
BOT_WEBHOOK_URL = 'https://webhook.my.bot.ru'

# Данные для авторизации в БД Postgresql. Главная рабочая БД
DB_NAME = 'database-name'
DB_USER = 'postgres'
DB_PASSWORD = ''
DB_HOST = '127.0.0.1'

# Таблица в БД Postgres для хранения запущенных PID (process ID)
PID_TABLE = 'pid_table'
PID_DEBUG_TABLE = 'pid_test_table'

# Сервер MongoDB. Используется ботом для Конечного Автомата (FSM - Finite State Machine)
MONGO_DB_HOST = '127.0.0.1'
MONGO_DB_PORT = 27017
MONGO_DB_NAME = 'aiogram_fsm'

# Данные для авторизации в системе биллинга
LAN_BILLING_USER = 'admin'
LAN_BILLING_PASSWORD = '<password>'
LAN_BILLING_URL = 'http://127.0.0.1/admin/soap/api3.wsdl'
LAN_BILLING_LOCATION = 'http://127.0.0.1:34012'

# Список WAN IP адресов, которым разрешен Admin API функционал
HOST_IP_LIST = '<ip address>, <ip address>'

# [Бизнес процесс] Feedback-заявки
CARDINALIS_URL = 'http://127.0.0.1:5050'

# [Бизнес процесс] Телеграм логирование
TELEGRAM_NOTIFY_BOT_URL = 'http://127.0.0.1:6000/send_message'

# [Бизнес процесс] Альтернативный бот
SUPPORT_BOT = 'chatBot'
