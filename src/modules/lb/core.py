import asyncio

import httpx
import uvloop
from aiologger import Logger
from zeep import AsyncClient, Settings
from zeep.client import Factory
from zeep.exceptions import Fault
from zeep.transports import AsyncTransport

from config import LAN_BILLING_USER, LAN_BILLING_PASSWORD, LAN_BILLING_URL, LAN_BILLING_LOCATION
from src.utils import get_datetime, get_phone_number


class CustomAsyncClient(AsyncClient):
    """
    Класс предназначен для добавления возможности указывать remote-host в параметр port.binding_options['address']
    (по умолчанию '127.0.0.1'):

    >>> client = CustomAsyncClient('url_to_wsdl', address='remote_host')

    Это сделано с помощью переопределения метода '_get_port'
    """
    def __init__(self, wsdl, transport=None, settings=None, address=None, **kwargs):
        super().__init__(wsdl, transport=transport, settings=settings, **kwargs)
        self.address = address  # новый параметр
        self._get_port = self._get_port_deco(self._get_port)

    def _get_port_deco(self, get_port):
        def get_port_wrapper(service, name):
            port = get_port(service, name)
            port.binding_options.update({'address': self.address})
            return port
        return get_port_wrapper


class LanBillingCore:
    get_datetime = staticmethod(get_datetime)
    get_phone_number = staticmethod(get_phone_number)

    def __init__(self, logger: Logger = None):
        self.user = LAN_BILLING_USER
        self.__password = LAN_BILLING_PASSWORD
        self._api_url = LAN_BILLING_URL
        self._api_location = LAN_BILLING_LOCATION
        self.loop: uvloop.Loop = None
        self.client: CustomAsyncClient = None
        self.factory: Factory = None
        self._settings = Settings(raw_response=False)
        self._httpx_client: httpx.AsyncClient = httpx.AsyncClient(auth=(self.user, self.__password))
        self._wsdl_client: httpx.Client = httpx.Client(auth=(self.user, self.__password))
        self.logger = logger

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LanBillingCore, cls).__new__(cls)
        return cls.instance

    def __del__(self):
        try:
            if self.loop is not None and self.loop.is_running():
                self.loop.run_until_complete(self.close_connections())
            else:
                asyncio.run(self.close_connections())
        except:
            pass

    async def close_connections(self):
        if not self._httpx_client.is_closed:
            await self._httpx_client.aclose()
        try:
            await self.logout()
        except RuntimeError:
            pass

    def connect_api(self):
        if not self.client:
            self.client = CustomAsyncClient(self._api_url, settings=self._settings, address=self._api_location,
                                            transport=AsyncTransport(client=self._httpx_client,
                                                                     wsdl_client=self._wsdl_client))
            self.factory = self.client.type_factory('ns0')
        # self.client.service._binding_options.update({'address': self._api_location})
        if not self.logger:
            self.logger = Logger.with_default_handlers()

    async def login(self):
        if self.client is None:
            self.connect_api()
        try:
            await self.client.service.Login(self.user, self.__password)
        except Exception as e:
            await self.logger.warning(f'LBZeepCore logining error: {e}')
            return False
        else:
            return True

    async def logout(self):
        await self.client.service.Logout()

    async def execute(self, func, *args):
        try:
            return await self.client.service[func](*args)
        except Fault as e:
            if e.message == 'error_auth':
                if await self.login():
                    return await self.client.service[func](*args)
                else:
                    return []
            else:
                raise e

    async def direct_request(self, function, *args, try_again=False, pass_faults=False):
        if self.client is None:
            if not await self.login():
                return []
        try:
            res = await self.execute(function, *args)
        except Exception as e:
            if not try_again:
                return await self.direct_request(function, *args, try_again=True, pass_faults=pass_faults)
            else:
                if not pass_faults:
                    msg = f'LB request "{function}" error{f" [{args=}]" if args else ""}: {e}'
                    await self.logger.warning(msg)
                return []
        else:
            return res
