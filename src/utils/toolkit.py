import hashlib
import re
from datetime import datetime


__all__ = ('get_hash', 'map_format', 'get_datetime', 'get_phone_number')


def get_hash(text: str):
    return hashlib.md5(f'{datetime.now()}&{text}'.encode()).hexdigest()


def map_format(text: str, **kwargs):
    if text and kwargs:
        for key, value in kwargs.items():
            text = text.replace('{%s}' % key, str(value))
    return text


def get_datetime(date_str):
    if isinstance(date_str, datetime):
        return date_str.strftime('%Y-%m-%d %H:%M:%S')
    else:
        if ' ' not in date_str:
            date_str += ' 00:00:00'
        if '-' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(date_str, '%Y/%m/%d %H:%M:%S')


def get_phone_number(num):
    num = ''.join(re.findall(r'\d+', str(num)))[-10:]
    num = num if len(num) == 10 else ''
    if len(num) > 0 and num[0] == '9':
        return num
    else:
        return None
