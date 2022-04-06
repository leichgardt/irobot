import traceback

from aiologger import Logger

from src.modules import lb, sql
from src.web.schemas.table import Table
from src.web.utils import telegram_api


async def broadcast(data: dict, logger: Logger):
    """
    Функция массовой рассылки сообщений пользователям бота. Запускается через web-интерфейс

    Формат данных `data` {
        id: int                 - ID записи в БД в таблице irobot.mailings,
        type: str               - тип рассылка сообщения
        targets: list or None,  - список целей (для типов "direct", "user_id", "agrm_id", "agrm")
        text: str               - текст сообщения
        parse_mode: str         - метод парсинга для форматирования текста (html, markdown, markdown_v2, ...)
    }
    """
    if data:
        await sql.upd_mailing_status(data['id'], 'processing')
        try:
            if data['type'] == 'notify':
                targets = [data[0] for data in await sql.get_subs() if data]
            elif data['type'] == 'mailing':
                targets = [data[0] for data in await sql.get_subs(mailing=True) if data]
            elif data['type'] == 'direct':
                targets = data['targets']
            else:
                await logger.warning(f'Broadcast error [{data["id"]}]: wrong mail type ID "{data["type"]}"')
                await sql.upd_mailing_status(data['id'], 'error')
                return 0
        except Exception as e:
            await logger.error(f'Broadcast error [{data.get("id", 0) or data}]: {e}\n{traceback.format_exc()}')
            if data.get('id', 0):
                await sql.upd_mailing_status(data.get('id', 0), 'failed')
        else:
            if targets:
                for chat_id in set(targets):
                    await telegram_api.send_message(chat_id, data['text'], parse_mode=data['parse_mode'])
                await sql.upd_mailing_status(data['id'], 'complete')
            else:
                await logger.warning(f'Broadcast error [{data["id"]}]: failed to get targets {data["targets"]}')
                await sql.upd_mailing_status(data['id'], 'missed')


async def get_subscriber_table():
    accs = await sql.get_sub_accounts()
    if accs:
        data = {}
        for chat_id, login, mailing in accs:
            if chat_id not in data:
                data[chat_id] = dict(accounts=login, mailing=mailing)
            else:
                data[chat_id]['accounts'] = data[chat_id]['accounts'] + '<br/>' + login
        table = Table([[key, value['mailing'], value['accounts']] for key, value in data.items()])
        for line in table:
            if not line[1].value:
                line[1].style = 'background-color: red;'
            else:
                line[1].style = 'background-color: green; color: white;'
        return table.get_html()


async def get_mailing_history():
    res = await sql.get_mailings()
    if res:
        table = Table(res)
        for line in table:
            line[4].value = '\n'.join(line[4].value) if isinstance(line[4].value, list) else line[4].value
        return table.get_html()


async def distribute_message(text, parse_mode, target_type, target):
    mail_id, targets = 0, []
    if target_type == 'user_id':
        targets = [chat_id for uid in targets for chat_id in await sql.find_user_chats(uid)]
    elif target_type == 'chat_id':
        targets = [target]
    elif target_type in ['agrm_id', 'agrm']:
        accounts = await lb.direct_request('getAccounts',
                                           {'agrmid': target} if target_type == 'agrmid' else {'agrmnum': target})
        targets = [chat_id for acc in accounts for chat_id in await sql.find_user_chats(acc.account.uid)]
    if targets:
        mail_id = await sql.add_mailing('direct', text, list(set(targets)), parse_mode)
    return mail_id, targets
