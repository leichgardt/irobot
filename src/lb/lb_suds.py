import uvloop
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from suds.client import Client

from src.utils import config, logger, alogger, get_datetime, get_phone_number


class LBCore:
    get_datetime = get_datetime
    get_phone_number = get_phone_number

    def __init__(self):
        self.user = config['lanbilling']['user']
        self.__password = config['lanbilling']['password']
        self.agents = config['lanbilling']['agents']
        self._api_url = config['lanbilling']['url']
        self._api_location = config['lanbilling']['location']
        self.client: Client = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.loop: uvloop.loop = None

    def connect_api(self):
        self.client = Client(url=self._api_url, location=self._api_location, faults=False)

    def login(self):
        if self.client is None:
            self.connect_api()
        if self.client.service.Login(self.user, self.__password)[0] != 200:
            logger.warning('API logging error')

    def func(self, func, *args):
        return self.client.service['api3'][func](*args)

    async def async_direct_request(self, func, *args, pass_faults=False):
        if self.client is None:
            self.connect_api()
        try:
            res = self.func(func, *args)
        except Exception as e:
            await alogger.error(f'[directRequest]\n{e}')
        else:
            if res[0] != 200:
                if res[1].faultstring == 'error_auth' or ('detail' in res[1] and 'No logged person' in res[1].detail):
                    self.login()
                res = self.func(func, *args)
                if res[0] != 200:
                    if pass_faults:
                        return []
                    else:
                        await alogger.error(res[1])
            return res[1]

    def direct_request(self, func, *args, pass_faults=False):
        if self.client is None:
            self.connect_api()
        try:
            res = self.func(func, *args)
        except Exception as e:
            logger.error(f'[directRequest]\n{e}')
        else:
            if res[0] != 200:
                if res[1].faultstring == 'error_auth' or ('detail' in res[1] and 'No logged person' in res[1].detail):
                    self.login()
                res = self.func(func, *args)
                if res[0] != 200:
                    if pass_faults:
                        return []
                    else:
                        logger.error(res[1])
            return res[1]


lb = LBCore()


async def lb_request(*args, **kwargs):
    if lb.loop and lb.loop.is_running():
        return await lb.loop.run_in_executor(lb.executor, partial(lb.direct_request, *args, **kwargs))
    else:
        return await lb.async_direct_request(*args, **kwargs)
