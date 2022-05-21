from config import REDIS_URL
from src.modules.cache_storage.schemas.server_full import CacheServer
from src.modules.cache_storage.redis_engine import RedisEngine


async def main(cache_serv):
    res = await cache_serv.set('my-key', (1, 2, 3), 1)
    print('set', res)
    value = await cache_serv.get('my-key', tuple)
    print('value', value, type(value))
    res = await cache_serv.delete('my-key')
    print('del', res)


cache_server = CacheServer(RedisEngine(REDIS_URL))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main(cache_server))
