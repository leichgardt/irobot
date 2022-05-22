import asyncio

from src.modules import lb


async def make_payment(agrm_num, amount, receipt):
    count = 5
    while count > 0:
        record_id = await lb.new_payment(agrm_num, amount, receipt)
        if record_id:
            return record_id
        else:
            count -= 1
            if count > 0:
                await asyncio.sleep(5)
    return 0
