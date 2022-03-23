from datetime import datetime, timedelta

from src.lb.core import LBZeepCore
from src.utils import get_datetime


class LBAPI(LBZeepCore):
    async def check_account_pass(self, agrmnum: str, input_pass: str):
        """
        1  - access granted
        0  - access denied
        -1 - agreement not found
        """
        agrms = await self.direct_request('getAgreements', {'login': agrmnum})
        if agrms:
            for agrm in agrms:
                if agrm.closedon is None:
                    acc = await self.direct_request('getAccount', agrm.uid)
                    if acc:
                        return 1 if acc[0].account['pass'] == input_pass else 0
                    else:
                        await self.logger.warning(f'Getting account error: agrmnum={agrmnum}')
                        return 0
        return -1

    async def get_user_id_by_login(self, login: str):
        acc = await self.direct_request('getAccounts', dict(login=login))
        return acc[0].account.uid if acc else None

    async def get_account_agrms(self, login: str = '', agrm_id: int = 0):
        kwargs = dict(login=login) if login else dict(agrmid=agrm_id) if agrm_id else dict()
        if kwargs:
            agrms = await self.direct_request('getAgreements', dict(**kwargs))
            return [dict(agrm=agrm.number, agrm_id=agrm.agrmid, balance=round(agrm.balance, 2), credit=agrm.credit,
                         promisecredit=agrm.promisecredit, user_id=agrm.uid)
                    for agrm in agrms if agrm.closedon is None]
        return []

    async def get_balance(self, *, agrmnum: str = None, agrm_data: dict = None):
        if agrmnum:
            agrm = await self.direct_request('getAgreements', dict(agrmnum=agrmnum))
            balance = round(agrm[0].balance, 2)
            agrm_id = agrm[0].agrmid
        else:
            balance = agrm_data['balance']
            agrm_id = agrm_data['agrmid']
        data = dict(balance=balance)
        dtfrom = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d %H:%M:%S')
        promises = await self.direct_request('getPromisePayments', dict(agrmid=agrm_id, dtfrom=dtfrom))
        for promise in promises:
            if promise.payid == 0:
                data['credit'] = dict(sum=promise.debt, date=promise.promtill)
                data['balance'] += promise.amount
                break
        return data

    async def promise_available(self, agrm_data: dict):
        if agrm_data['balance'] >= -300:
            dtfrom = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            credit = await self.direct_request('getPromisePayments', {'agrmid': agrm_data['agrm_id'], 'dtfrom': dtfrom})
            for cre in credit:
                if cre.payid == 0:
                    return False
        else:
            return False
        return True

    async def promise_payment(self, agrm_id, amount):
        return await self.direct_request('PromisePayment', agrm_id, amount, pass_faults=True)

    async def get_payments(self, agrm: str, **kwargs):
        res = await self.direct_request('getAgreements', dict(agrmnum=agrm))
        if res:
            dtto = datetime.now()
            dtfrom = dtto - timedelta(**kwargs)
            return await self.direct_request('getPayments', dict(agrmid=res[0].agrmid,
                                                                 dtfrom=get_datetime(dtfrom),
                                                                 dtto=get_datetime(dtto)))

    async def new_payment(self, agrm: str, amount: float, receipt: str, paydate: [str, datetime] = None, test=False):
        res = await self.direct_request('getAgreements', dict(agrmnum=agrm))
        if res:
            paydate = paydate or datetime.now()
            agrm_id = res[0].agrmid
            try:
                payment_obj = self.factory.soapPayment(
                    agrmid=agrm_id,
                    currid=1,
                    classid=1 if not test else 2,
                    amount=amount,
                    cashcode=1,
                    classname='Безналично',
                    receipt=f'{"test-" if test else ""}{receipt}',
                    comment='IroBot via Sberbank',
                    localdate=self.get_datetime(datetime.now()),
                    paydate=paydate if isinstance(paydate, str) else self.get_datetime(paydate)
                )
                await self.logger.info(f'Payment try [{agrm_id=} {agrm=} {amount=} {receipt=} {paydate=}]')
                return await self.direct_request('Payment', payment_obj)
            except Exception as e:
                await self.logger.error(f'LB Payment error: {e} [{agrm_id=} {agrm=} {amount=} {receipt=} {paydate=}]')
        return 0


lb = LBAPI()

if __name__ == '__main__':
    import asyncio

    res = asyncio.run(lb.get_account_agrms('05275'))
    print(res)
