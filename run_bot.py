__author__ = 'leichgardt'

import traceback
from datetime import datetime
from src.bot import run_bot

try:
    loop = run_bot()
    loop.run_forever()
except Exception as e:
    print(e)
    with open('/tmp/irobot.log', 'a') as f:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f'[{date}] Exception: {e}\n\n{traceback.format_exc()}\n{"#" * 40}\n')
