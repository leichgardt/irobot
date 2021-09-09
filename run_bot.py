__author__ = 'leichgardt'

import traceback
from datetime import datetime
from src.bot import run_bot

try:
    run_bot()
except Exception as e:
    print('Irobot Exception:', e)
    with open('/tmp/irobot.log', 'a') as f:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'[{date}] Exception: {e}\n{traceback.format_exc()}\n{"#" * 60}')
