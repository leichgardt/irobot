from typing import Union, List

from aiogram import types
from aiogram.dispatcher import FSMContext

from src.bot import keyboards
from src.bot.api.api import edit_inline_message
from src.bot.core import bot
from src.lb import lb
from src.parameters import HOST_URL, SBER_TOKEN, RECEIPT_EMAIL
from src.sql import sql
from src.text import Texts
from src.utils import logger, get_hash


__all__ = (
    'finish_review',
    'get_payment_hash',
    'get_promise_payment_agrms',
    'get_agrm_balances',
    'get_all_agrm_data',
    'get_login_url',
    'send_payment_invoice',
    'save_dialog_message'
)


async def finish_review(chat_id: int, state: FSMContext, comment: str, rating: int):
    await state.finish()
    if rating:
        text, parse_mode = Texts.review_result_full.pair(comment=comment, rating=rating)
    else:
        text, parse_mode = Texts.review_result_comment.pair(comment=comment)
    await edit_inline_message(chat_id, text, parse_mode, reply_markup=None)
    await answer_to_review(chat_id, rating)


async def answer_to_review(chat_id: int, rating: int):
    kb = keyboards.main_menu_kb
    if rating and rating == 5:
        await bot.send_message(chat_id, *Texts.review_done_best.pair(), reply_markup=kb)
    else:
        await bot.send_message(chat_id, *Texts.review_done.pair(), reply_markup=kb)


def get_payment_hash(chat_id: int, agreement_num: str):
    return get_hash(f'{chat_id}&{agreement_num}')


def get_payment_price(agrm: str, amount: Union[int, float], tax: Union[int, float] = None):
    """ Получить список товаров для онлайн оплаты (Telegram Payments 2.0 - for invoice) """
    return [types.LabeledPrice(label=Texts.payment_item_price.format(agrm=agrm), amount=int(amount * 100))] + \
           ([types.LabeledPrice(label=Texts.payment_item_tax, amount=int(tax * 100))] if tax else [])


def get_login_url(hash_code: str):
    return '{}login?hash_code={}'.format(HOST_URL, hash_code)


async def get_agrm_balances(chat_id: int):
    """ Получить текст с балансом всех договоров для пользователя """
    await logger.info(f'Balance check [{chat_id}]')
    text = []
    data = await get_all_agrm_data(chat_id, only_numbers=True)
    if data:
        for agrms in data.values():
            for agrm in agrms:
                bal = await lb.get_balance(agrmnum=agrm)
                if bal:
                    text.append(Texts.balance.format(agrm=agrm, summ=bal['balance']))
                    if 'credit' in bal:
                        text[-1] += Texts.balance_credit.format(cre=bal['credit']['sum'],
                                                                date=bal["credit"]["date"].split(' ')[0])
    else:
        text = Texts.balance_no_agrms,
    return '\n'.join(text), Texts.balance.parse_mode


async def get_all_agrm_data(chat_id: int, *, only_numbers=False):
    """
    Получить список всех договоров (только номера договоров или полные данные)
    :param chat_id: ID чата.
    :param only_numbers: вывести только номера договоров без загрузки полной информации о них.
    """
    output = {}
    accounts = await sql.get_accounts(chat_id)
    for account in accounts:
        agrms = await lb.get_account_agrms(account)
        for agrm in agrms:
            if only_numbers:
                output[account] = [agrm['agrm'] for agrm in agrms]
            else:
                output[agrm['agrm_id']] = agrm
    return output if only_numbers else list(output.values())


async def get_promise_payment_agrms(agrms: List[str]) -> List[str]:
    """
    Договоры, доступные для обещанного платежа для определённого чата `chat_id` или из предоставленного списка `agrms`
    """
    output = []
    if agrms:
        for agrm in agrms:
            if await lb.promise_available(agrm):
                output.append(agrm)
    return output


async def send_payment_invoice(chat_id, hash_code, agreement, amount, payload):
    return await bot.send_invoice(
        chat_id,
        provider_token=SBER_TOKEN,
        provider_data=dict(
            tax_system_code=0,
            customer=dict(
                email=RECEIPT_EMAIL,
            ),
            items=[dict(
                description=Texts.payment_description.format(agrm=agreement, amount=amount),
                quantity='1.0',
                amount=dict(
                    value=amount,
                    currency='RUB'
                ),
                vat_code=1,
            ), ],
        ),
        title=Texts.payment_title,
        description=Texts.payment_description_item.format(agrm=agreement, amount=amount),
        currency='RUB',
        prices=get_payment_price(agreement, amount),
        payload=payload,
        start_parameter=f'payment-{hash_code}',
    )


async def save_dialog_message(message: types.Message, user: str):
    if message.content_type == 'text':
        data = {'text': message.text}
    elif message.content_type == 'document':
        data = {'file_id': message.document.file_id, 'mime_type': message.document.mime_type}
    elif message.content_type == 'photo':
        data = {'file_id': message.photo[-1].file_id}
    elif message.content_type == 'sticker':
        data = {'file_id': message.sticker.file_id}
    elif message.content_type == 'voice':
        data = {'file_id': message.voice.file_id}
    elif message.content_type == 'video':
        data = {'file_id': message.video.file_id, 'mime_type': message.video.mime_type}
    elif message.content_type == 'video_note':
        data = {'file_id': message.video_note.file_id}
    elif message.content_type == 'audio':
        data = {'file_id': message.audio.file_id, 'mime_type': message.audio.mime_type}
    else:
        await logger.warning(f'Unhandled support message content type: {message} [{message.chat.id}]')
        return
    data = {'caption': message.caption, **data} if 'caption' in message else data
    await sql.add_support_message(message.chat.id, message.message_id, user, message.content_type, data)
