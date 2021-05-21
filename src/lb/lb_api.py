from src.lb.lb_suds import lb_request
from src.utils import alogger

from datetime import datetime, timedelta


async def check_account_pass(agrmnum, input_pass):
    """
    1  - access granted
    0  - access denied
    -1 - agreement not found
    """
    agrm = await lb_request('getAgreements', {'agrmnum': agrmnum})
    if agrm:
        if agrm[0].closedon is None:
            acc = await lb_request('getAccount', agrm[0].uid)
            if acc:
                return 1 if acc[0].account['pass'] == input_pass else 0, agrm[0].agrmid
            else:
                await alogger.warning(f'Getting account error: agrmnum={agrm}')
                return 0, None
    return -1, None


async def get_balance(agrmnum):
    data = {}
    agrm = await lb_request('getAgreements', {'agrmnum': agrmnum})
    if agrm:
        agrm = agrm[0]
        data.update({'balance': agrm.balance})
        dtfrom = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        credit = await lb_request('getPromisePayments', {'agrmid': agrm.agrmid, 'dtfrom': dtfrom})
        for cre in credit:
            if cre.payid == 0:
                data.update({'credit': {'sum': cre.debt, 'date': cre.promtill}})
                data['balance'] += cre.amount
                break
    return data


async def promise_available(agrm_id):
    agrm = await lb_request('getAgreements', {'agrmid': agrm_id})
    if agrm:
        agrm = agrm[0]
        if agrm.balance >= -300:
            dtfrom = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            credit = await lb_request('getPromisePayments', {'agrmid': agrm.agrmid, 'dtfrom': dtfrom})
            for cre in credit:
                if cre.payid == 0:
                    return False
        else:
            return False
    return True


async def promise_payment(agrm_id, amount):
    return await lb_request('PromisePayment', agrm_id, amount, pass_faults=True)
