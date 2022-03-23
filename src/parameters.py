from src.utils import config

MONGO_DB_HOST = config['paladin']['cup']
MONGO_DB_PORT = 27017
MONGO_DB_NAME = 'aiogram_fsm'

SBER_TOKEN = config['sberbank']['token']

DB_NAME = config['postgres']['dbname']
DB_USER = config['postgres']['dbuser']
DB_HOST = config['postgres']['dbhost']

CARDINALIS_URL = 'https://{}/cardinalis'.format(config['paladin']['cup-domain'])

HOST_URL = 'https://{}/irobot/'.format(config['paladin']['maindomain'])

API_TOKEN = config['irobot']['token']

SHOP_ID = config['yandex']['shop-id']
SECRET_KEY = config['yandex']['secret-key']
RECEIPT_EMAIL = config['yandex']['email']

PID_TABLE = 'pids'

WEBHOOK_HOST = 'https://{}/irobot_webhook'.format(config['paladin']['maindomain'])
