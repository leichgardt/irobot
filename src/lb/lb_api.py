from datetime import datetime, timedelta

from src.lb.lb_zeep import lb
from src.utils import get_datetime, is_async_logger



async def check_account_pass(agrmnum: str, input_pass: str):
    """
    1  - access granted
    0  - access denied
    -1 - agreement not found
    """
    agrms = await lb.direct_request('getAgreements', {'login': agrmnum})
    if agrms:
        for agrm in agrms:
            if agrm.closedon is None:
                acc = await lb.direct_request('getAccount', agrm.uid)
                if acc:
                    return 1 if acc[0].account['pass'] == input_pass else 0
                else:
                    if is_async_logger(lb.logger):
                        await lb.logger.warning(f'Getting account error: agrmnum={agrmnum}')
                    else:
                        lb.logger.warning(f'Getting account error: agrmnum={agrmnum}')
                    return 0
    return -1


async def get_account_agrms(login: str):
    agrms = await lb.direct_request('getAgreements', dict(login=login))
    return [dict(agrm=agrm.number, agrm_id=agrm.agrmid, balance=round(agrm.balance, 2), credit=agrm.credit,
                 promisecredit=agrm.promisecredit, user_id=agrm.uid)
            for agrm in agrms if agrm.closedon is None]


async def get_balance(*, agrmnum: str = None, agrm_data: dict = None):
    if agrmnum:
        agrm = await lb.direct_request('getAgreements', dict(agrmnum=agrmnum))
        balance = round(agrm[0].balance, 2)
        agrm_id = agrm[0].agrmid
    else:
        balance = agrm_data['balance']
        agrm_id = agrm_data['agrmid']
    data = dict(balance=balance)
    dtfrom = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S')
    promises = await lb.direct_request('getPromisePayments', dict(agrmid=agrm_id, dtfrom=dtfrom))
    for promise in promises:
        if promise.payid == 0:
            data['credit'] = dict(sum=promise.debt, date=promise.promtill)
            data['balance'] += promise.amount
            break
    return data


async def promise_available(agrm_data: dict):
    if agrm_data['balance'] >= -300:
        dtfrom = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        credit = await lb.direct_request('getPromisePayments', {'agrmid': agrm_data['agrm_id'], 'dtfrom': dtfrom})
        for cre in credit:
            if cre.payid == 0:
                return False
    else:
        return False
    return True


async def promise_payment(agrm_id, amount):
    return await lb.direct_request('PromisePayment', agrm_id, amount, pass_faults=True)


async def get_payments(agrm: str, **kwargs):
    res = await lb.direct_request('getAgreements', dict(agrmnum=agrm))
    if res:
        dtto = datetime.now()
        dtfrom = dtto - timedelta(**kwargs)
        return await lb.direct_request('getPayments', dict(agrmid=res[0].agrmid, dtfrom=get_datetime(dtfrom), dtto=get_datetime(dtto)))


async def payment(agrm: str, amount: float, receipt: str, paydate: [str, datetime]):
    res = await lb.direct_request('getAgreements', dict(agrmnum=agrm))
    if res:
        try:
            payment_obj = lb.factory.soapPayment(
                agrmid=res[0].agrmid,
                currid=1,
                classid=1,
                amount=amount,
                cashcode=1,
                classname='Безналично',
                receipt=receipt,
                comment='IroBot via YooKassa',
                localdate=lb.get_datetime(datetime.now()),
                paydate=paydate if isinstance(paydate, str) else lb.get_datetime(paydate)
            )
            return await lb.direct_request('Payment', payment_obj)
        except Exception as e:
            if is_async_logger(lb.logger):
                await lb.logger.error(f'LB Payment error: {e}')
            else:
                lb.logger.error(f'LB Payment error: {e}')
    return 0
