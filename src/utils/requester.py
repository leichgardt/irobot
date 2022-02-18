import aiohttp
from .logger import alogger


async def post_request(*args, _as_json=True, _logger=alogger, **kwargs):
    res = None
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(*args, **kwargs) as resp:
                if resp.status == 200:
                    if _as_json:
                        res = await resp.json()
                    else:
                        res = resp
                else:
                    await _logger.info(f'Bad status [{resp.status}] for {resp.url}')
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError):
            await _logger.info(f'Can\'t connect to server "{resp.url}"')
        except Exception as e:
            await _logger.warning(f'Connection error: {e}')
    return res
