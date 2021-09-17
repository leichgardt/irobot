from src.utils import config

HOST_URL = 'https://{}/irobot/'.format(config['paladin']['maindomain'])

API_TOKEN = config['irobot']['token']

SHOP_ID = config['yandex']['shop-id']
SECRET_KEY = config['yandex']['secret-key']
RECEIPT_EMAIL = config['yandex']['email']

PID_TABLE = 'pids'

WEBHOOK_HOST = 'https://{}/irobot_webhook'.format(config['paladin']['maindomain'])
