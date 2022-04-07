from src.utils import config


VERSION = '1.1.1'
ABOUT = """Веб-приложение IroBot-web предназначено для рассылки новостей и уведомлений пользователям бота @{}, 
а так же для обработки запросов платежей от системы Yoomoney.\n
Сервис регистрирует новые платежи и мониторит их выполнение через систему LanBilling; и при обнаружении 
завершенного платежа сервис уведомляет пользователя через бота об успешной оплате.
"""

TEST_CHAT_ID = config['irobot']['me']
SUPPORT_BOT = config['irobot']['chatbot']

HOST_IP_LIST = config['paladin']['ironnet-global']

LANBILLING_USER = config['lanbilling']['user']
LANBILLING_PASSWORD = config['lanbilling']['password']
LANBILLING_URL = config['lanbilling']['url']
LANBILLING_LOCATION = config['lanbilling']['location']

TELEGRAM_NOTIFY_BOT_URL = 'https://{}/tesseract/api/notify'.format(config['paladin']['cup-domain'])

MONGO_DB_HOST = config['paladin']['cup']
MONGO_DB_PORT = 27017
MONGO_DB_NAME = 'aiogram_fsm'

SBER_TOKEN = config['sberbank']['token']

DB_NAME = config['postgres']['dbname']
DB_USER = config['postgres']['dbuser']
DB_HOST = config['postgres']['dbhost']

CARDINALIS_URL = 'https://{}/cardinalis'.format(config['paladin']['cup-domain'])

HOST_URL = 'https://{}/irobot'.format(config['paladin']['maindomain'])

API_TOKEN = config['irobot']['token']

SHOP_ID = config['yandex']['shop-id']
SECRET_KEY = config['yandex']['secret-key']
RECEIPT_EMAIL = config['yandex']['email']

PID_TABLE = 'pids'

WEBHOOK_HOST = 'https://{}/irobot_webhook'.format(config['paladin']['maindomain'])
