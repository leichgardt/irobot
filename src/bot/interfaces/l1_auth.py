from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.bot.api import private_and_login_require, exc_handler
from src.bot.schemas import keyboards, Keyboard
from src.bot.utils.login import get_login_url
from src.modules import sql, Texts
from src.utils import logger, get_hash

try:
    from .l0_test import bot, dp

    print('>>> The Test layer L0 was loaded.')
except ImportError:
    from src.bot.core import bot, dp


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
                               reply_markup=keyboards.main_menu_kb)
    else:
        await logger.info(f'Start [{message.chat.id}]')
        text = Texts.start.format(name=(message.from_user.first_name or message.from_user.last_name
                                        or message.from_user.username))
        hash_code = get_hash(message.chat.id)
        url = get_login_url(hash_code)
        res = await bot.send_message(message.chat.id, text, Texts.start.parse_mode,
                                     reply_markup=Keyboard.inline(keyboards.get_login_btn(url)))
        await sql.add_chat(message.chat.id, res.message_id, text, Texts.start.parse_mode, hash_code,
                           message.from_user.username, message.from_user.first_name, message.from_user.last_name)
