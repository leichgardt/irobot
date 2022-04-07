from datetime import datetime
from functools import wraps
from ipaddress import ip_address, ip_network
from urllib.parse import urlparse, parse_qs

from fastapi import Request, Response

from parameters import ABOUT, HOST_IP_LIST, VERSION

__all__ = (
    'get_query_params',
    'get_request_data',
    'lan_require',
    'get_context'
)


def get_query_params(url):
    """ Парсинг параметров URL запроса """
    return parse_qs(urlparse(url).query)


async def get_request_data(request: Request):
    """ Получить переданные данные из запроса (типа: JSON, FORM, QUERY_PARAMS)"""
    if request.method == 'GET':
        data = request.query_params
    else:
        try:
            data = await request.json()
        except:
            data = await request.form()
    return dict(data) if data else {}


def lan_require(func):
    """ Декоратор-ограничитель: разрешает доступ, если IP-адрес запроса из локальной сети или от сервера """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = [arg for arg in args if isinstance(arg, Request)]
        if not request:
            request = [arg for arg in kwargs.values() if isinstance(arg, Request)]
        if not request:
            return Response(status_code=500)
        ip = request[0].client.host or '127.0.0.1'
        lan_networks = [ip_network('192.168.0.0/16'), ip_network('172.16.0.0/12'), ip_network('10.0.0.0/8')]
        if (ip in ['localhost', '0.0.0.0', '127.0.0.1'] or ip in HOST_IP_LIST or
                [True for network in lan_networks if ip_address(ip) in network]):
            return await func(*args, **kwargs)
        else:
            return Response(status_code=403)
    return wrapper


def get_context(request: Request, **kwargs):
    return {
        'request': request,
        'timestamp': int(datetime.now().timestamp()),
        'title': 'Irobot Admin',
        'pages': [
            {'title': 'Чат', 'url': 'chat'},
            {'title': 'Рассылка', 'url': 'mailing'},
        ],
        'about': ABOUT,
        'version': VERSION,
        'oper': {},
        **kwargs
    }
