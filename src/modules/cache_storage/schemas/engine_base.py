from abc import ABC, abstractmethod
from typing import Union

from aioredis import ConnectionPool, Redis


NumericT = Union[bytes, int, float]
TextT = Union[str]
CollectionT = Union[tuple, list, dict, set, frozenset]  # типы данных, сохраняемые в JSON-виде

KeyT = Union[NumericT, TextT]  # стандартные типы данных, возвращаемые Redis
AllKeysT = Union[NumericT, TextT, CollectionT]
FullKeysT = Union[AllKeysT, None]


class BaseEngine(ABC):
    core: Redis = None
    pool: ConnectionPool = None

    def __init__(self, url: str):
        self.url = url

    @abstractmethod
    def connect_to_server(self):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def set(self, name: str, value: KeyT, expire: int = None) -> bool:
        pass

    @abstractmethod
    async def get(self, name: str) -> bytes:
        pass

    @abstractmethod
    async def delete(self, *names: str) -> int:
        pass

    @abstractmethod
    def get_pubsub(self):
        pass

    @abstractmethod
    async def publish(self, channel: str, message: KeyT):
        pass
