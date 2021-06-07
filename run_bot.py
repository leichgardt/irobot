__author__ = 'leichgardt'

import traceback

from src.bot import run_bot

try:
    loop = run_bot()
    loop.run_forever()
except Exception as e:
    with open('/tmp/bot.log', 'w') as f:
        f.write(f'Exception: {e}\n\n{traceback.format_exc()}\n{"#" * 40}\n')
