from .kb_main_menu import *
from .kb_settings import *
from .kb_payment import *
from .kb_agrms import *
from src.utils import logger


async def get_keyboard_menu(menu: str, chat_id=None):
    parse_mode = None

    if menu in ('main', 'main-menu'):
        text = '@ironnet_bot\nГлавное меню'
        buttons = main_menu_btn

    elif menu == 'help':
        text = 'Помощь\n\nС помощью этого бота ты можешь\:\n\- проверять свой __баланс__\n\- __пополнять__ счёт\n\- ' \
               'менять __тариф__\n\- добавить несколько учётных записей через __настройки__\n\- и следить за всеми ' \
               'добавленными договорами\n\n*Команды*\n/start \- начать работу\n/help \- увидеть это сообщение\n' \
               '/settings \- настроить бота после авторизации'
        buttons = help_btn
        parse_mode = types.ParseMode.MARKDOWN_V2

    elif menu == 'settings':
        text = 'Настройки\n\nВыбери любой интересующий тебя пункт настроек.'
        buttons = settings_menu_btn

    elif menu == 'exit':
        text = 'Уверен, что хочешь выйти? :cry:'
        buttons = exit_confirm_btn

    elif menu == 'cancel':
        text = 'Отмена'
        buttons = cancel_btn

    elif menu == 'agrms':
        text = 'Настройки >> Договоры\n\nДобавь ещё договор или удали добавленные.'
        buttons = await get_agrms_btn(chat_id) + agrms_settings_btn

    elif menu == 'agrm':
        text = 'Удалять не обязательно, можно просто отключить уведомления в настройках уведомлений :wink:\nНо удалив' \
               ' договор, ты не сможешь проверять баланс, и мы не сможем предупредить тебя, если деньги будут' \
               ' заканчиваться! :scream:'
        buttons = agrm_control_btn

    elif menu == 'notify':
        text = 'Настройки >> Уведомления\n\nМы будем уведомлять тебя, если что-то произойдёт. Например, заранее ' \
               'сообщим о работах, когда интернет будет недоступен!\nОтключи уведомления, если они тебе мешают, но ' \
               'из-за этого нам будет очень грустно :disappointed:\n\nВ новостных рассылках мы будем рассказывать ' \
               'тебе об акциях, скидках и о других интересных вещах, которые происходят у нас в Айроннет! :blush:'
        buttons = await get_notify_settings_btn(chat_id) + notify_settings_btn

    elif menu == 'payments':
        text = 'Как хочешь пополнить счёт?'
        buttons = payment_choice_btn

    elif menu == 'payments-agrm':
        text = 'Обещанный платёж\n\nОбещанный платёж на сумму 100 руб. на 5 дней. Если на балансе договора менее 300 ' \
               'рублей, то подключить эту услугу <u>нельзя</u>.\n\nВыбери, счёт какого договора пополнить.'
        buttons = await get_payment_btn(chat_id) + back_to_main
        parse_mode = types.ParseMode.HTML

    elif menu == 'payments-amount':
        text = 'Выбери сумму, на которую хочешь пополнить счёт, или введи её сам.'
        buttons = {}

    elif menu == 'confirm':
        text = 'Вы уверены?'
        buttons = confirm_btn

    else:
        logger.info(f'Bad keyboard getting: menu={menu}; chat_id={chat_id}')
        return None, None, {}
    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
    for row in buttons:
        row_btns = []
        for params in row:
            payload = {}
            for key, value in params.items():
                payload.update({key: emojize(value) if key == 'text' else value})
            row_btns.append(types.InlineKeyboardButton(**payload))
        # row_btns = (types.InlineKeyboardButton(**params) for params in row)
        # for payload in row:
        keyboard_markup.row(*row_btns)
    return emojize(text), keyboard_markup, parse_mode


async def get_reply_keyboard_menu(menu: str, chat_id=None):
    if menu == 'start':
        text = 'Отправь /start чтобы начать.'
        buttons = start_r_btn
    else:
        return '', None
    keyboard_markup = types.ReplyKeyboardMarkup(row_width=3)
    for row in buttons:
        row_btns = (types.KeyboardButton(**params) for params in row)
        keyboard_markup.row(*row_btns)
    return emojize(text), keyboard_markup


# async def get_inline_keyboard(*menus, chat_id=None):
#     menu_list = []
#     for menu in menus:
#         if menu == 'back':
#             menu_list.append(back_to_main)
#         elif menu == 'settings':
#             menu_list.append(settings_menu_btn)
#         elif menu == 'exit':
#             menu_list.append(exit_confirm_btn)
#         elif menu == 'agrms':
#             menu_list.append(await get_agrms_btn(chat_id))
#         elif menu == 'agrms-settings':
#             menu_list.append(agrms_settings_btn)
#         elif menu == 'agrm':
#             menu_list.append(agrm_control_btn)
#         elif menu == 'notify':
#             menu_list.append(await get_notify_settings_btn(chat_id))
#         elif menu == 'payments':
#             menu_list.append(payment_choice_btn)
#         elif menu == 'payments-amount':
#             menu_list.append('')
#         elif menu == 'confirm':
#             menu_list.append(confirm_btn)
#         else:
#             logger.info(f'Menu {menu} doesn\'t exist')
#     keyboard_markup = types.InlineKeyboardMarkup(row_width=3)
#     for menu in menu_list:
#         for row in menu:
#             row_btns = (types.InlineKeyboardButton(**params) for params in row)
#             keyboard_markup.row(*row_btns)
#     return keyboard_markup
