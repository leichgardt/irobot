import aiohttp
from .logger import alogger


async def request(*args, **kwargs):
    res = None
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(*args, **kwargs) as resp:
                if resp.status == 200:
                    res = resp
                else:
                    await alogger.info(f'Bad status [{resp.status}] for {resp.url}')
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
            await alogger.info(f'Can\'t connect to server "{resp.url}"')
        except Exception as e:
            await alogger.warning(f'Connection error: {e}')
    return res
