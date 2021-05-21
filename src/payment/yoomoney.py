import json

from src.utils import config, request


async def yoomoney_pay(agrmnum: str, amount: float):
    """
    yandex money yookassa яндекс деньги

    https://yookassa.ru/docs/payment-solution/payment-form/basics
    """
    url = 'https://yoomoney.ru/eshop.xml'
    payload = {
        'shopId': config['yandex']['shop-id'],
        'scid': config['yandex']['sc-id'],
        'sum': amount,
        'customerNumber': agrmnum,
        'shopSuccesURL': config['yandex']['success-url'],
        'shopFailURL': config['yandex']['fail-url'],
        'paymentType': 'AC',
    }
    data = {
        'customer': {
            # 'fullName': 'ололошкин хряк тестостеронович',
            # 'phone': '79110000000',
            'email': config['yandex']['email'],  # finance department
        },
        'taxSystem': 2,
        'items': [
            {
                'quantity': 1,
                'price': {'amount': payload['sum']},
                'tax': 1,
                'text': f'Услуги доступа к сети Интернет по договору №{payload["customerNumber"]}',
                'paymentMethodType': 'full_payment',
                'paymentSubjectType': 'service'
             }
        ]
    }
    payload.update({'ym_merchant_receipt': json.dumps(data)})
    res = await request(url, data=payload)
    return str(res.url) if res else res
