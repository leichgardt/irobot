import aiohttp
from .logger import logger


async def request(*args, **kwargs):
    res = {}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(*args, **kwargs) as resp:
                if resp.status == 200:
                    res = await resp.json()
                else:
                    logger.info(f'Bad status [{resp.status}] for {resp.url}')
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
            logger.info(f'Can\'t connect to server "{resp.url}"')
        except Exception as e:
            logger.warning(f'Connection error: {e}')
    return res
