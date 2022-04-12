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


async def set_new_password(oper_id: int, new_password: str):
    salt = get_random_string()
    hashed_password = hash_password(new_password, salt)
    res = await sql.execute(
        'UPDATE irobot.operators SET hashed_password= %s WHERE oper_id=%s RETURNING hashed_password',
        f'{salt}${hashed_password}', oper_id, fetch_one=True
    )
    return res[0] == f'{salt}${hashed_password}'


async def get_oper_by_login(login: str):
    return await sql.execute('SELECT * FROM irobot.operators WHERE login=%s', login, fetch_one=True, as_dict=True)


async def get_oper_by_token(token: str) -> oper_schema.Oper:
    res = await sql.execute(
        'SELECT o.oper_id, o.login, o.full_name, o.oper_id, o.enabled, o.root '
        'FROM irobot.operators o JOIN irobot.tokens t ON o.oper_id = t.oper_id WHERE t.expires > now() AND t.token=%s',
        token, fetch_one=True, as_dict=True
    )
    return oper_schema.Oper(**res) if res else None


async def create_oper_token(oper_id: int):
    res = await sql.execute('INSERT INTO irobot.tokens (expires, oper_id) VALUES (%s, %s) RETURNING token, expires',
                            datetime.now() + timedelta(days=2), oper_id, as_dict=True, fetch_one=True)
    res['expires'] = res['expires'].timestamp()
    return res


async def create_oper(oper: oper_schema.OperCreate):
    salt = get_random_string()
    hashed_password = hash_password(oper.password, salt)
    oper_db = await sql.execute(
        'INSERT INTO irobot.operators (login, full_name, hashed_password, root) VALUES (%s, %s, %s, %s) '
        'RETURNING oper_id, enabled', oper.login, oper.full_name, f'{salt}${hashed_password}', oper.root, fetch_one=True
    )
    return {**oper.dict(), 'oper_id': oper_db[0], 'enabled': oper_db[1]}
