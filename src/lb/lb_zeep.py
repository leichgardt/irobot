import asyncio
import httpx
import zeep.exceptions
import uvloop

from zeep import AsyncClient, Settings
from zeep.wsdl import Document
from zeep.transports import AsyncTransport

from src.utils import config, alogger, is_async_logger, get_datetime, get_phone_number


class CustomAsyncClient(AsyncClient):
    """
    Данный кастомный класс предназначен для добавления возможности указывать remote-host
    в параметр port.binding_options['address'] (по умолчанию '127.0.0.1'):

    >>> client = CustomAsyncClient('url_to_wsdl', address='remote_host')

    Это сделано с помощью переопределения метода '_get_port'
    """
    def __init__(self, wsdl, transport=None, settings=None, address=None):
        self.settings = settings or Settings()
        self.transport = (
            transport if transport is not None else self._default_transport()
        )
        self.wsdl = Document(wsdl, self.transport, settings=self.settings)
        self.wsse = None
        self.plugins = []
        self._default_service = None
        self._default_service_name = None
        self._default_port_name = None
        self._default_soapheaders = None
        self.address = address  # новый параметр

    def _get_port(self, service, name):
        if name:
            port = service.ports.get(name)
            if not port:
                raise ValueError("Port not found")
        else:
            port = list(service.ports.values())[0]
        port.binding_options.update({'address': self.address})
        return port


class LBZeepCore:
    get_datetime = get_datetime
    get_phone_number = get_phone_number

    def __init__(self, logger=alogger):
        self.user = config['lanbilling']['user']
        self.__password = config['lanbilling']['password']
        self._api_url = config['lanbilling']['url']
        self._api_location = config['lanbilling']['location']
        self.loop: uvloop.Loop = None
        self.client: CustomAsyncClient = None
        self._settings = Settings(raw_response=False)
        self._httpx_client: httpx.AsyncClient = httpx.AsyncClient(auth=(self.user, self.__password))
        self._wsdl_client: httpx.Client = httpx.Client(auth=(self.user, self.__password))
        self.logger = logger

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LBZeepCore, cls).__new__(cls)
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
        self.client = CustomAsyncClient(self._api_url, settings=self._settings, address=self._api_location,
                                        transport=AsyncTransport(client=self._httpx_client,
                                                                 wsdl_client=self._wsdl_client))
        # self.client.service._binding_options.update({'address': self._api_location})

    async def login(self):
        if self.client is None:
            self.connect_api()
        try:
            await self.client.service.Login(self.user, self.__password)
        except Exception as e:
            if is_async_logger(self.logger):
                await self.logger.warning(e)
            else:
                self.logger.warning(e)
            return False
        else:
            return True

    async def logout(self):
        await self.client.service.Logout()

    async def func(self, func, *args):
        try:
            return await self.client.service[func](*args)
        except zeep.exceptions.Fault as e:
            if e.message == 'error_auth':
                if await self.login():
                    return await self.client.service[func](*args)
                else:
                    return []
            else:
                raise e

    async def direct_request(self, func, *args, try_again=False, pass_faults=False):
        if self.client is None:
            if not await self.login():
                return []
        try:
            res = await self.func(func, *args)
        except Exception as e:
            if not try_again:
                return await self.direct_request(func, *args, try_again=True, pass_faults=pass_faults)
            else:
                if not pass_faults:
                    if is_async_logger(self.logger):
                        await self.logger.warning(e)
                    else:
                        self.logger.warning(e)
                return []
        else:
            return res


lb = LBZeepCore()


async def lb_request(*args, **kwargs):
    return await lb.direct_request(*args, **kwargs)
