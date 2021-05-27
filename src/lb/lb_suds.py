import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from suds.client import Client
from datetime import datetime

from src.utils import config, logger, alogger, get_datetime, get_phone_number


class LBCore:
    def __init__(self):
        self.user = config['lanbilling']['user']
        self.__password = config['lanbilling']['password']
        self.agents = config['lanbilling']['agents']
        self._api_url = config['lanbilling']['url']
        self._api_location = config['lanbilling']['location']
        self.client = None
        self.get_datetime = get_datetime
        self.get_phone_number = get_phone_number
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.loop = None

    def connect_api(self):
        self.client = Client(url=self._api_url, location=self._api_location, faults=False)

    def login(self):
        start = datetime.now()
        logger.info('API logging...')
        if self.client is None:
            self.connect_api()
        if self.client.service.Login(self.user, self.__password)[0] == 200:
            end = datetime.now() - start
            logger.info(f'API login success in {end}')
        else:
            logger.error('API logging error')

    def func(self, func, *args):
        return self.client.service['api3'][func](*args)

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
                    logger.debug('\n'.join(['%s: %s' % (k, v) for k, v in dict(res[1]).items()]))
                    if pass_faults:
                        logger.info(res[1])
                        return []
                    else:
                        logger.error(res[1])
            return res[1]


lb = LBCore()


async def lb_request(*args, **kwargs):
    if lb.loop is None:
        lb.loop = asyncio.get_event_loop()
    await alogger.debug(f'LB request: {args} & {kwargs}')
    return await lb.loop.run_in_executor(lb.executor, partial(lb.direct_request, *args, **kwargs))


if __name__ == '__main__':
    start_time = datetime.now()

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(lb_request('getAccount', 0))
    print(res)

    print('Spent time:', datetime.now() - start_time)
