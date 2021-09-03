from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize

from src.utils import map_format


class T(str):
    def __init__(self, value=''):
        self.__str__ = value
        self.answer = ''
        self.parse_mode = None

    def __call__(self, new_str: str):
        """ Обновить значение переменной текста T внутри класса Texts """
        new_t = T(new_str)
        new_t.parse_mode = self.parse_mode
        new_t.answer = self.answer
        return new_t

    def full(self, **kwargs):
        """ Вернуть текст и его параметры. Формат вывода: (answer, text, parse_mode) """
        return (map_format(self.answer, **kwargs),
                map_format(self.__str__, **kwargs),
                map_format(self.parse_mode, **kwargs))


class Texts:
    start = T(
        'Привет, {name}!\nС помощью этого бота ты сможешь проверять баланс, пополнять счета и ещё многое '
        'другое!\nНо сначала давай авторизуемся!')
    non_private = T(
        'Извини, я работаю только в приватном чате.')
    non_auth = T(
        'Чтобы использовать бота, тебе надо авторизоваться.\nОтправь мне команду /start')
    cancel = T(
        'Отменено.')
    cancel.answer = \
        'Отмена'

    auth_success = T(emojize(
        'Ты успешно авторизовался под учётной записью {account} :tada:\nДобро пожаловать! :smile:\n\n'
        'Отправь мне команду\n/balance - чтобы узнать баланс своего договора\n'
        '/help - чтобы узнать, что я могу'))

    settings = T(
        'Настройки\n\nВыбери пункт настроек.')
    settings_non_auth = T(
        'Чтобы настраивать бота, тебе надо авторизоваться, отправив команду /start')
    settings_done = T(
        'Настройки сохранены.')
    settings_done.answer = \
        'Настройки сохранены'
    settings_accounts = T(
        'Настройки >> Учётные записи\n\n{accounts}\n\nДобавь ещё одну учётную запись или удали добавленные.')
    settings_accounts.answer = \
        'Настройки договоров'
    settings_account = T(
        'Настройки >> Учётные записи >> {account}\n\nМожешь удалить учётную запись из своего Телеграм-аккаунта.')
    settings_account.answer = \
        'Настройки учётной записи {account}'
    settings_account_del_answer = T(
        'Учётная запись {account} удалена')
    settings_account_add = T(
        'Настройки >> Учётные записи >> Добавить\n\nЧтобы добавить ещё одну учётную запись, нажми на кнопку '
        '"Авторизоваться".')
    settings_account_add.answer = \
        'Добавить новую учётную запись'
    settings_account_add_success = T(emojize(
        'Учётная запись {account} успешно добавлена :tada:'))
    settings_notify = T(emojize(
        'Настройки >> Уведомления\n\nВ рассылках я буду рассказывать тебе об акциях, скидках и о '
        'других интересных вещах, которые происходят у нас в Айроннет! :blush:\n\nВыключи, если не хочешь получать '
        'новостную рассылку.'))
    settings_notify.answer = \
        'Настройки уведомлений'
    settings_notify_enable = T(emojize(
        'Настройки >> Уведомления\n\nВ рассылках я буду рассказывать тебе об акциях, скидках и о '
        'других интересных вещах, которые происходят у нас в Айроннет! :blush:\n\nВключи, если хочешь получать '
        'новостную рассылку.'))
    settings_notify_enable.answer = settings_notify.answer
    settings_notify_switch_answer = T(
        'Уведомления переключены')
    settings_mailing_switch_answer = T(
        'Новости переключены')
    settings_exit = T(emojize(
        'Уверен, что хочешь выйти? :cry:'))
    settings_exit.answer = \
        'Выйти?'
    settings_exited = T(emojize(
        'Ты успешно вышел. Возвращайся по-скорее! :smile:\nОтправь /start чтобы начать.'))
    settings_exited.answer = \
        'Успешный выход'

    main_menu = T(emojize(
        'Чем {} может тебе помочь?\nВыбери пункт меню снизу :point_down:'))
    main_menu.answer = \
        'Главное меню'

    balance = T(
        'Баланс договора <b>№{agrm}</b>:\n{summ} руб.\n')
    balance.parse_mode = ParseMode.HTML
    balance.answer = \
        'Баланс'
    balance_credit = T(
        'Обещанный платёж:\n{cre} руб. до {date}\n')
    balance_credit.parse_mode = balance.parse_mode
    balance_no_agrms = T(
        'У тебя нет добавленных договоров. Добавь их в Настройках Учётных записей /settings')

    review = T(
        'Отзыв\n\nНа сколько звёзд от 1 до 5 меня оценишь? Или можешь просто написать, что обо мне думаешь.')
    review.answer = \
        'Оставить отзыв'
    review_rate = T(
        'Отзыв\n\n<b>Оценка</b>: {rating}\nНапиши отзыв или отправь оценку.')
    review_rate.answer = \
        'Оценил на {rating}!'
    review_with_comment = T(
        'Отзыв\n\n<b>Отзыв</b>: {comment}\n\nНапиши новое сообщение, чтобы изменить свой отзыв, или отправь этот.')
    review_full = T(
        'Отзыв\n\n<b>Оценка</b>: {rating}\n<b>Отзыв</b>: {comment}\n\nНапиши новое сообщение, чтобы изменить свой '
        'отзыв, или отправь это.')
    review_result_full = T(
        '<b>Оценка</b>: {rating}\n<b>Отзыв</b>: {comment}')
    review_result_rate = T(
        '<b>Оценка</b>: {rating}')
    review_result_comment = T(
        '<b>Отзыв</b>: {comment}')
    review_rate.parse_mode = ParseMode.HTML
    review_with_comment.parse_mode = review_rate.parse_mode
    review_full.parse_mode = review_rate.parse_mode
    review_result_full.parse_mode = review_rate.parse_mode
    review_result_rate.parse_mode = review_rate.parse_mode
    review_result_comment.parse_mode = review_rate.parse_mode
    review_done = T(emojize(
        'Отзыв успешно отправлен!\nСпасибо тебе! Мы обязательно учтём твоё мнение :blush:'))
    review_done.answer = \
        'Отзыв отправлен'
    review_done_best = T(emojize(
        'Отзыв успешно отправлен :party:\nСпасибо огромное! Мы стараемся изо всех сил :blush:'))
    review_done_best.answer = review_done.answer

    help = T(
        'Помощь\n\nС помощью этого бота ты можешь\:\n\- проверять свой __баланс__\n\- __пополнять__ счёт\n'
        '\- добавить несколько учётных записей через __настройки__\n\- и следить за всеми добавленными '
        'договорами\n\n*Команды*\n/start \- начать работу\n/help \- увидеть это сообщение\n/settings \- настроить бота')
    help.parse_mode = ParseMode.MARKDOWN_V2
    help.answer = \
        'Помощь'
    help_auth = T(
        help + '\n\nЧтобы использовать бота, тебе надо авторизоваться, отправив команду /start')
    help_auth.parse_mode = ParseMode.MARKDOWN_V2

    about_us = T(
        '{} - телеграм-бот компании ООО "Айроннет" 2021\n\nДля связи с тех. поддержкой звоните по тел. '
        '8-800-222-46-69')

    payments = T(
        'Платежи\n\nКак хочешь пополнить счёт?')
    payments.answer = \
        'Платежи'
    payments_promise = T(
        'Платежи >> Обещанный платёж\n\nВыбери, счёт какого договора пополнить.')
    payments_promise.answer = \
        'Обещанный платёж'
    payments_promise_offer = T(
        'Платежи >> Обещанный платёж\n\nПодключить обещанный платёж на 100 руб. к договору №{agrm}? Его нужно будет '
        'погасить за 5 дней.')
    payments_promise_offer.answer = \
        'Выбран договор {agrm}'
    payments_promise_success = T(emojize(
        'Успех! Обещанный платёж успешно подключен! :tada:'))
    payments_promise_success.answer = \
        'Обещанный платёж успешно подключен!'
    payments_promise_fail = T(
        'Ошибка! Не удалось подключить обещанный платёж. Попробуй еще раз или обратитесь в тех.поддержку.')
    payments_promise_fail.answer = \
        'Не удалось подключить обещанный платёж.'
    payments_promise_already_have = T(
        'На договоре №{agrm} уже подключен обещанный платёж. Погаси долг, чтобы взять следующий обещанный платёж.')
    payments_promise_already_have.answer = \
        'Уже подключен на договоре №{agrm}'

    payments_online = T(
        'Платежи >> Оплата Онлайн\n\nВыбери, счёт какого договора пополнить.')
    payments_online.answer = \
        'Оплата Онлайн'
    payments_online_amount = T(
        'Платежи >> Оплата Онлайн\n\nДоговор №{agrm}\nБаланс: {balance} руб.\n\nНа сколько хочешь пополнить счёт?\n\n'
        'Введи сумму.')
    payments_online_amount.answer = payments_promise_offer.answer
    payments_online_amount_is_not_digit = T(emojize(
        'Платежи >> Оплата Онлайн\n\nНе понимаю, о чем ты :hmm: Введи сумму, на которую хочешь пополнить счёт.'))
    payments_online_offer = T(emojize(
        'Платежи >> Оплата онлайн >> Договор №{agrm}\n\nК зачислению: {amount} руб.\n'
        'Комиссия (до 4%): {tax} руб.\n\nИтого к оплате: <u>{res} руб.</u>\n\n'
        'Можешь переслать сообщение со счётом другу, чтобы он оплатил его тебе :smiley:'))
    payments_online_offer.parse_mode = ParseMode.HTML
    payments_online_success = T(
        'Оплата успешно прошла! Деньги на счёт поступят в ближайшие пару минут!')
    payments_online_success_short = T(
        'Оплата успешно прошла!')
    payments_online_fail = T(
        'Не удалось провести платёж.')
    payment_error = T(
        'Ошибка платежа. Попробуй ещё раз или обратись в службу технической поддержки')
    payments_online_already_have = T(
        'Этот счёт уже был оплачен.')
    payment_item_price = T(
        'Услуги доступа к сети Интернет по договору №{agrm}')
    payment_item_tax = T(
        'Комиссия (до 4%)')
    payment_title = T(
        'Пополнение счёта договора №{agrm}')
    payment_description = T(
        'Пополнить счёт договора №{agrm} на {amount} руб.')
    payment_error_message = T(
        'Не удалось провести платёж. Попробуйте ещё раз.')
    payments_on_process = T(
        'Платёж обрабатывается.')
    payments_online_was_paid = T(emojize(
        'Твой счёт на {amount} руб. только что оплатили :star_struck: Скоро средства поступят на твой баланс!'))
    payments_after_for_guest = T(
        'Ты можешь авторизоваться!\nДля этого отправь мне /start')

    backend_error = T(
        'Непредвиденная ошибка!')

    new_feedback = T(
        'Ты поможешь стать нам лучше, если оценишь работу наших сотрудников (от 1 до 5), выполнивших твою заявку!')
    best_feedback = T(emojize(
        'Спасибо! Мы очень стараемся! :blush:'))
    best_feedback.answer = emojize(
        'Превосходно! 5 из 5! :party:')
    why_feedback = T(
        'Можешь написать, чего не хватило до пятёрки?')
    why_feedback.answer = emojize(
        'Что не так? :disappointed:')
    got_feedback = T(emojize(
        'Обязательно передам это моим руководителям! Спасибо, что уделил время :relaxed: Ты помогаешь нам стать лучше!'))
    end_feedback_answer = \
        'Спасибо за оценку!'

    def get_account_agrm_list(data: dict):
        text = []
        for account, agrms in data.items():
            text += [f'Учетная запись: {account}\n']
            text[-1] += f'Договор: №{agrms[0]}' if len(agrms) == 1 else \
                'Договоры:\n' + '\n'.join([f' - №{agrm}' for agrm in agrms])
        return '\n\n'.join(text)
