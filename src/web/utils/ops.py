import hashlib
import random
import string
from datetime import datetime, timedelta

from src.modules import sql
from src.web.schemas import ops as oper_schema


def get_random_string(length=12):
    """ Генерирует случайную строку, использующуюся как соль """
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = get_random_string()
    enc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return enc.hex()


def validate_password(password: str, hashed_password: str):
    salt, hashed = hashed_password.split("$")
    return hash_password(password, salt) == hashed


async def get_oper_by_login(login: str):
    res = await sql.execute('select * from irobot.operators where login=%s', login, as_dict=True)
    return res[0] if res else []


async def get_oper_by_token(token: str):
    res = await sql.execute('select o.login, o.full_name, o.oper_id, o.enabled from irobot.operators o '
                            'join irobot.tokens t on o.oper_id = t.oper_id where t.expires > now() and t.token=%s',
                            token, as_dict=True)
    return res[0] if res else []


async def create_oper_token(oper_id: int):
    res = await sql.execute('insert into irobot.tokens (expires, oper_id) VALUES (%s, %s) returning token, expires',
                            datetime.now() + timedelta(days=2), oper_id, as_dict=True)
    return res[0] if res else None


async def create_oper(oper: oper_schema.OperCreate):
    salt = get_random_string()
    hashed_password = hash_password(oper.password, salt)
    oper_id = await sql.insert('insert into irobot.operators (login, full_name, hashed_password) values (%s, %s, %s) '
                               'returning oper_id', oper.login, oper.full_name, f'{salt}${hashed_password}')
    token = await create_oper_token(oper_id)
    token_dict = {'token': token['token'], 'expires': token['expires']}

    return {**oper.dict(), 'id': oper_id, 'is_active': True, 'token': token_dict}
