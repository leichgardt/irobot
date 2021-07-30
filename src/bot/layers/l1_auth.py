from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, private_and_login_require, get_keyboard, get_hash, get_login_url, run_cmd
from src.bot import keyboards
from src.bot.text import Texts

try:
    from .l0_test import bot, dp
    print('>>> The Test layer L0 was loaded.')
except ImportError:
    from src.bot.bot_core import bot, dp


@dp.message_handler(Text('старт', ignore_case=True), state='*')
@dp.message_handler(commands='start', state='*')
@private_and_login_require(do_not_check_sub=True)
async def start_cmd_h(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start

    Функция посылает клиенту Главное меню, если он авторизован, или начинает процесс авторизации:
    - создание хэш-кода;
    - регистрация чата;
    - создание URL-ссылки на форму регистрации через HTTP

    Далее форма авторизации обрабатывается Web-приложением в главном модуле app.py по адресам "/login" и "/api/login"
    """
    await run_cmd(bot.send_chat_action(message.chat.id, 'typing'))
    await state.finish()
    if await sql.get_sub(message.from_user.id):
        await run_cmd(bot.send_message(message.chat.id, text=Texts.main_menu, parse_mode=Texts.main_menu.parse_mode,
                                       reply_markup=main_menu))
    else:
        await alogger.info(f'Start [{message.chat.id}]')
        text = Texts.start.format(name=message.from_user.first_name)
        hash_code = get_hash(message.chat.id)
        url = get_login_url(hash_code)
        res = await run_cmd(bot.send_message(message.chat.id, text, Texts.start.parse_mode,
                                             reply_markup=get_keyboard(keyboards.get_login_btn(url))))
        await sql.add_chat(message.chat.id, res.message_id, text, Texts.start.parse_mode, hash_code,
                           message.from_user.as_json())
