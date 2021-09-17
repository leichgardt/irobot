import asyncio
import uuid

from datetime import datetime, timedelta
from threading import Thread, Lock
from yookassa import Payment
from yookassa import Configuration

from src.parameters import SHOP_ID, SECRET_KEY, HOST_URL, RECEIPT_EMAIL
from src.text import Texts
from src.utils import get_phone_number, alogger

Configuration.account_id = SHOP_ID
Configuration.secret_key = SECRET_KEY

tmp = {}


async def yoomoney_pay(agrm: str, amount: [int, float], tax: [int, float], hash_code: str) -> dict:
    """
    :return словарь с ключами {url, id}
    """
    global tmp
    lock = Lock()

    def await_payment_url(agrm, amount, tax, hash_code):
        global tmp
        with lock:
            payment = create_payment(agrm, amount, tax, hash_code)
            tmp[hash_code] = dict(url=payment.confirmation.confirmation_url, id=payment.id)

    start = datetime.now()
    thr = Thread(target=await_payment_url, args=(agrm, amount, tax, hash_code))
    thr.daemon = True
    thr.start()
    while thr.is_alive() or datetime.now() - start > timedelta(seconds=5):
        try:
            await asyncio.sleep(0.1)
        except Exception as e:
            await alogger.error(e)
            break
    payment = tmp.get(hash_code, {})
    tmp.pop(hash_code)
    return payment


def create_payment(agrm: str, amount: [int, float], tax: [int, float], hash_code: str,
                   email: str = None, phone: str = None):
    idempotence_key = str(uuid.uuid4())
    params = dict(
        amount=dict(
          value=amount + tax,
          currency='RUB'
        ),
        description=Texts.payment_description.format(agrm=agrm, amount=amount),
        capture=True,
        confirmation=dict(
            type='redirect',
            return_url=f'{HOST_URL}payment?hash_code={hash_code}',
        ),
        metadata=dict(
            payment_id=-1,  # для совместимости с платежами через сайт
            hash_code=hash_code
        ),
        receipt=dict(
            items=[
                dict(
                    description=Texts.payment_description_item.format(agrm=agrm),
                    quantity='1.0',
                    amount=dict(
                        value=amount + tax,
                        currency='RUB'
                    ),
                    vat_code=1,
                    payment_subject='service',
                ),
            ],
            tax_system_code=2,
            customer=dict()
        )
    )
    if email:
        params['receipt']['customer']['email'] = email
    elif phone:
        params['receipt']['customer']['phone'] = f'7{get_phone_number(phone)}'
    else:
        params['receipt']['customer']['email'] = RECEIPT_EMAIL
    return Payment.create(params, idempotence_key)


if __name__ == '__main__':
    print(start := datetime.now())
    kek = asyncio.run(yoomoney_pay('05275', 100, 3, '123'))
    # kek = new_payment('05275', 100, '123')
    print(datetime.now() - start)
    print(kek)
