from src.bot.schemas import keyboards, Keyboard
from src.bot.utils.agreements import get_all_agrm_data
from src.modules import lb, sql, Texts
from src.web.utils import telegram_api


async def logining(chat_id: int, login: str):
    """ Авторизация пользователя по chat_id и логину от Личного Кабинета (ЛК) """
    await telegram_api.send_chat_action(chat_id, 'typing')
    user_id = await lb.get_user_id_by_login(login)
    await sql.add_account(chat_id, login, user_id)
    await sql.upd_hash(chat_id, None)
    if not await sql.get_sub(chat_id):
        # если пользователь новый
        await sql.subscribe(chat_id)
        inline, _, _ = await sql.get_inline_message(chat_id)
        await telegram_api.delete_message(chat_id, inline)
        text, parse_mode = Texts.auth_success.pair()
        await telegram_api.send_message(chat_id, text.format(account=login), parse_mode,
                                        reply_markup=keyboards.main_menu_kb)
    else:
        # если пользователь добавил новый аккаунт
        text, parse_mode = Texts.settings_account_add_success.pair()
        await telegram_api.edit_inline_message(chat_id, text.format(account=login), parse_mode)
        data = await get_all_agrm_data(chat_id, only_numbers=True)
        text, parse_mode = Texts.settings_accounts.pair(accounts=Texts.get_account_agrm_list(data))
        btn_list = await keyboards.get_agrms_btn(custom=data, prefix='account') + [keyboards.account_settings_btn]
        kb = Keyboard(btn_list).inline()
        await telegram_api.send_message(chat_id, text, parse_mode, reply_markup=kb)
