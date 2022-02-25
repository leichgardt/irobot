import ujson

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, private_and_login_require, get_keyboard, get_hash, get_login_url, exc_handler
from src.bot import keyboards
from src.text import Texts

try:
    from .l0_test import bot, dp

    print('>>> The Test layer L0 was loaded.')
except ImportError:
    from src.bot.bot_core import bot, dp


# async def start_payment(chat_id, payload):
#     """ Отправить счёт, если его собирается оплатить другой пользователь """
#     if payload and 'payment-' in payload:
#         hash_code = payload.replace('payment-', '')
#         payment = await sql.find_payment(hash_code)
#         if payment:
#             if payment['status'] != 'finished':
#                 await bot.send_invoice(**get_invoice_params(
#                     chat_id, payment['agrm'], payment['amount'], get_payment_tax(payment['amount']), hash_code
#                 ))
#             else:
#                 _, text, parse = Texts.payments_online_already_have.full()
#                 await bot.send_message(chat_id, text, parse, reply_markup=main_menu)
#         return True
#     return False


@dp.message_handler(Text('старт', ignore_case=True), state='*')
@dp.message_handler(commands='start', state='*')
@dp.async_task
@private_and_login_require(do_not_check_sub=True)
@exc_handler
async def start_cmd_h(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start

    Функция посылает клиенту Главное меню, если он авторизован, или начинает процесс авторизации:
    - создание хэш-кода;
    - регистрация чата;
    - создание URL-ссылки на форму регистрации через HTTP

    Далее форма авторизации обрабатывается Web-приложением в главном модуле app.py по адресам "/login" и "/api/login"
    """
    await bot.send_chat_action(message.chat.id, 'typing')
    await state.finish()
    # payload = message.get_args()  # в payload передаётся hash_code платежа
    # if payload:
    #     if await start_payment(message.chat.id, payload):
    #         return
    if await sql.get_sub(message.from_user.id):
        await bot.send_message(message.chat.id, text=Texts.main_menu, parse_mode=Texts.main_menu.parse_mode,
                               reply_markup=main_menu)
    else:
        await alogger.info(f'Start [{message.chat.id}]')
        text = Texts.start.format(name=(message.from_user.first_name or message.from_user.last_name
                                        or message.from_user.username))
        hash_code = get_hash(message.chat.id)
        url = get_login_url(hash_code)
        res = await bot.send_message(message.chat.id, text, Texts.start.parse_mode,
                                     reply_markup=get_keyboard(keyboards.get_login_btn(url)))
        await sql.add_chat(message.chat.id, res.message_id, text, Texts.start.parse_mode, hash_code,
                           message.from_user.username, message.from_user.first_name, message.from_user.last_name)
