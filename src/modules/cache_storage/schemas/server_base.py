from abc import ABC, abstractmethod
from typing import Union

from .engine_base import BaseEngine, KeyT, AllKeysT


class CacheServerBase(ABC):

    def __init__(self, engine: BaseEngine = None):
        self.api = engine

    @staticmethod
    def check_connection(func):
        async def wrapper(self, *args, **kwargs):
            if not self.api.core:
                self.api.connect_to_server()
            res = await func(self, *args, **kwargs)
            return res
        return wrapper

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    def prepare_data(self, value: AllKeysT) -> KeyT:
        pass

    @abstractmethod
    async def set(self, name: str, value: KeyT, expire: int = None) -> bool:
        pass

    @abstractmethod
    async def get(self, name: str, convert: type = None) -> Union[AllKeysT, None]:
        pass

    @abstractmethod
    async def delete(self, *names: str):
        pass

    @abstractmethod
    async def publish(self, channel: str, message: AllKeysT):
        pass
