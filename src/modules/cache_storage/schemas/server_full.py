from typing import Union

import ujson

from .engine_base import KeyT, AllKeysT
from .server_base import CacheServerBase


class CacheServer(CacheServerBase):

    def connect(self):
        self.api.connect_to_server()

    async def close(self):
        await self.api.close()

    def prepare_data(self, value: AllKeysT) -> KeyT:
        if isinstance(value, (dict, list, tuple)):
            return ujson.dumps(value)
        elif isinstance(value, (set, frozenset)):
            return ujson.dumps(list(value))
        else:
            return value

    @CacheServerBase.check_connection
    async def set(self, name: str, value: AllKeysT, expire: int = None) -> bool:
        return await self.api.set(name, self.prepare_data(value), expire)

    @CacheServerBase.check_connection
    async def get(self, name: str, convert: type = None) -> Union[AllKeysT, None]:
        res = await self.api.get(name)
        if convert and res:
            if convert in (dict, list, tuple, set):
                res = convert(ujson.loads(res))
            else:
                res = convert(res)
        return res

    @CacheServerBase.check_connection
    async def delete(self, *names: str):
        return await self.api.delete(*names)

    @CacheServerBase.check_connection
    async def publish(self, channel: str, data: AllKeysT):
        return await self.api.publish(channel, self.prepare_data(data))
