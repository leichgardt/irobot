from datetime import datetime, timedelta

from src.modules.lb.core import LanBillingCore


class LanBillingAPI(LanBillingCore):
    async def check_account_pass(self, agrm_num: str, input_pass: str):
        """
        1  - access granted
        0  - access denied
        -1 - agreement not found
        """
        agrms = await self.direct_request('getAgreements', {'login': agrm_num})
        if agrms:
            for agrm in agrms:
                if agrm.closedon is None:
                    acc = await self.direct_request('getAccount', agrm.uid)
                    if acc:
                        return 1 if acc[0].account['pass'] == input_pass else 0
                    else:
                        await self.logger.warning(f'Getting account error: agrmnum={agrm_num}')
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

    async def get_balance(self, *, agrm_num: str = None, agrm_data: dict = None):
        if agrm_num:
            agrm = await self.direct_request('getAgreements', dict(agrmnum=agrm_num))
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
            dt_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            credit = await self.direct_request('getPromisePayments', {'agrmid': agrm_data['agrm_id'],
                                                                      'dtfrom': dt_from})
            for cre in credit:
                if cre.payid == 0:
                    return False
        else:
            return False
        return True

    async def promise_payment(self, agrm_id, amount):
        return await self.direct_request('PromisePayment', agrm_id, amount, pass_faults=True)

    async def get_payment(self, record_id: int):
        res = await self.direct_request('getPayments', dict(recordid=record_id))
        return res[0] if res else {}

    async def new_payment(
            self,
            agrm_num: str,
            amount: float,
            receipt: str,
            payment_date: [str, datetime] = None,
            test=False
    ) -> int:
        res = await self.direct_request('getAgreements', dict(agrmnum=agrm_num))
        if res:
            payment_date = payment_date or datetime.now()
            agrm_id = res[0].agrmid
            receipt = receipt or datetime.now().strftime('%Y%m%d%H%M%S-%f')
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
                    paydate=payment_date if isinstance(payment_date, str) else self.get_datetime(payment_date)
                )
                await self.logger.info(f'Payment try [{agrm_id=} {agrm_num=} {amount=} {receipt=} {payment_date=}]')
                return await self.direct_request('Payment', payment_obj)
            except Exception as e:
                await self.logger.error(
                    f'LB Payment error: {e} [{agrm_id=} {agrm_num=} {amount=} {receipt=} {payment_date=}]'
                )
        return 0


lb = LanBillingAPI()

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(lb.get_account_agrms('05275')))
