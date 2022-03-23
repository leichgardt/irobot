from typing import Union

from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize

from src.utils import map_format


__all__ = ('Texts',)


class BaseText:
    text: str
    answer: str
    parse_mode: ParseMode


class ButtonText(BaseText):

    def __init__(
            self,
            text: Union[str, BaseText],
            *,
            answer: str = None,
            parse_mode: ParseMode = None
    ):
        self.text = emojize(str(text))
        self.__str__ = self.text
        self.answer = emojize(str(answer)) if answer else ''
        self.parse_mode = parse_mode

    def __repr__(self):
        return self.text

    def __str__(self):
        return self.text

    def __add__(self, other):
        return ButtonText(self.text + emojize(str(other)), answer=self.answer, parse_mode=self.parse_mode)

    def __call__(self, new_str: str):
        """ Обновить значение переменной текста T внутри класса Texts """
        return ButtonText(new_str, answer=self.answer, parse_mode=self.parse_mode)

    def __format__(self, format_spec):
        return self.text

    def format(self, *args, **kwargs):
        return self.text.format(*args, **kwargs)

    def full(self, **kwargs):
        """ Вернуть текст и его параметры. Формат вывода: (answer, text, parse_mode) """
        return map_format(self.answer, **kwargs), map_format(self.text, **kwargs), self.parse_mode

    def pair(self, **kwargs):
        """ Вернуть текст и его parse_mode. Формат вывода: (text, parse_mode) """
        return map_format(self.text, **kwargs), self.parse_mode


class Web:
    auth = 'Авторизация'
    error = 'Ошибка'
    login_try_again = [
        'Пожалуйста, начни авторизацию из <a href="https://t.me/{bot_name}">бота</a> заново.<br/>'
        'Если ошибка повторяется, <a href="https://t.me/{support}">напиши нам в поддержку</a>.'
    ]
    auth_success = 'Успешная авторизация!'
    payment_error = 'Ошибка платежа'
    payment_err_detail = ['Не удалось обработать платёж.<br/>Создай новый платёж и попробуй снова.']
    payment_success = 'Успешный платёж!'
    payment_processing = 'Подождите'
    payment_process_detail = ['<center>Платёж обрабатывается.</center>']
    backend_error = 'Ой, что-то пошло не так...<br/><small>(Ошибка 500)</small>'
    backend_err_detail = ['<center>Попробуй повторить операцию позже.</center>']


class Texts:
    web = Web

    me = ButtonText(
        '{name}'
    )

    start = ButtonText(
        'Привет, {name}!\nС помощью этого бота ты сможешь проверять баланс, пополнять счета и ещё многое '
        'другое!\nНо сначала давай авторизуемся!'
    )
    non_private = ButtonText(
        'Извини, я работаю только в приватном чате.'
    )
    non_auth = ButtonText(
        'Чтобы использовать бота, тебе надо авторизоваться.\nОтправь мне команду /start'
    )
    cancel = ButtonText(
        'Отменено',
        answer='Отмена'
    )
    back = ButtonText(
        'Назад',
        answer='Назад'
    )
    passed = ButtonText(
        'Пропустить',
        answer='Пропущено'
    )

    auth_success = ButtonText(
        'Ты успешно авторизовался под учётной записью {account} :tada:\nДобро пожаловать! :smile:\n\n'
        'Отправь мне команду\n/balance - чтобы узнать баланс своего договора\n'
        '/help - чтобы узнать, что я могу'
    )

    settings = ButtonText(
        'Настройки\n\nВыбери пункт настроек.'
    )
    settings_non_auth = ButtonText(
        'Чтобы настраивать бота, тебе надо авторизоваться, отправив команду /start'
    )
    settings_done = ButtonText(
        'Настройки сохранены.',
        answer='Настройки сохранены'
    )
    settings_accounts = ButtonText(
        'Настройки >> Учётные записи\n\n{accounts}\n\nДобавь ещё одну учётную запись или удали добавленные.',
        answer='Настройки договоров'
    )
    settings_account = ButtonText(
        'Настройки >> Учётные записи >> {account}\n\nМожешь удалить учётную запись из своего Телеграм-аккаунта.',
        answer='Настройки учётной записи {account}'
    )
    settings_account_del_answer = ButtonText(
        'Учётная запись {account} удалена'
    )
    settings_account_add = ButtonText(
        'Настройки >> Учётные записи >> Добавить\n\nЧтобы добавить ещё одну учётную запись, нажми на кнопку '
        '"Авторизоваться".',
        answer='Добавить новую учётную запись'
    )
    settings_account_add_success = ButtonText(
        'Учётная запись {account} успешно добавлена :tada:'
    )
    settings_notify = ButtonText(
        'Настройки >> Уведомления\n\nВ рассылках я буду рассказывать тебе об акциях, скидках и о '
        'других интересных вещах, которые происходят у нас в Айроннет! :blush:\n\nВыключи, если не хочешь получать '
        'новостную рассылку.',
        answer='Настройки уведомлений'
    )
    settings_notify_enable = ButtonText(
        'Настройки >> Уведомления\n\nВ рассылках я буду рассказывать тебе об акциях, скидках и о '
        'других интересных вещах, которые происходят у нас в Айроннет! :blush:\n\nВключи, если хочешь получать '
        'новостную рассылку.',
        answer=settings_notify.answer
    )
    settings_notify_switch_answer = ButtonText(
        'Уведомления переключены'
    )
    settings_mailing_switch_answer = ButtonText(
        'Новости переключены'
    )
    settings_exit = ButtonText(
        'Уверен, что хочешь выйти? :cry:',
        answer='Выйти?'
    )
    settings_exited = ButtonText(
        'Ты успешно вышел. Возвращайся по-скорее! :smile:\nОтправь /start чтобы начать.',
        answer='Успешный выход'
    )

    main_menu = ButtonText(
        'Чем {} может тебе помочь?\nВыбери пункт меню снизу :point_down:',
        answer='Главное меню'
    )

    balance = ButtonText(
        'Баланс договора №{agrm}:\n<b>{summ} руб.</b>\n',
        answer='Баланс',
        parse_mode=ParseMode.HTML
    )

    balance_credit = ButtonText(
        'Включая обещанный платёж:\n<u>{cre} руб.</u> до {date}\n',
        parse_mode=balance.parse_mode
    )
    balance_no_agrms = ButtonText(
        'У тебя нет добавленных договоров. Добавь их в Настройках Учётных записей /settings'
    )

    review = ButtonText(
        'Отзыв\n\nНа сколько звёзд от 1 до 5 меня оценишь? Напиши, что обо мне думаешь?',
        answer='Оставить отзыв'
    )
    review_rate = ButtonText(
        'Отзыв\n\n<b>Оценка</b>: {rating}\nНапиши отзыв или отправь оценку.',
        answer='Оценил на {rating}!',
        parse_mode=ParseMode.HTML
    )
    review_with_comment = ButtonText(
        'Отзыв\n\n<b>Отзыв</b>: {comment}\n\nНапиши новое сообщение, чтобы изменить свой отзыв, или отправь этот.',
        parse_mode=review_rate.parse_mode
    )
    review_full = ButtonText(
        'Отзыв\n\n<b>Оценка</b>: {rating}\n<b>Отзыв</b>: {comment}\n\nНапиши новое сообщение, чтобы изменить свой '
        'отзыв, или отправь это.',
        parse_mode=review_rate.parse_mode
    )
    review_result_full = ButtonText(
        '<b>Оценка</b>: {rating}\n<b>Отзыв</b>: {comment}',
        parse_mode=review_rate.parse_mode
    )
    review_result_rate = ButtonText(
        '<b>Оценка</b>: {rating}',
        parse_mode=review_rate.parse_mode
    )
    review_result_comment = ButtonText(
        '<b>Отзыв</b>: {comment}',
        parse_mode=review_rate.parse_mode
    )
    review_done = ButtonText(
        'Отправил твой отзыв!\nСпасибо тебе! Мы обязательно учтём твоё мнение :blush:',
        answer='Отзыв отправлен'
    )
    review_done_best = ButtonText(
        'Отправил твой отзыв :partying_face:\nСпасибо огромное! Мы стараемся изо всех сил :blush:',
        answer=review_done.answer
    )

    help = ButtonText(
        'Помощь\n\nС помощью этого бота ты можешь\:\n\- проверять свой __баланс__\n\- __пополнять__ счёт\n'
        '\- добавить несколько учётных записей через __настройки__\n\- и следить за всеми добавленными '
        'договорами\n\n*Команды*\n/start \- начать работу\n/help \- увидеть это сообщение\n/settings \- настроить бота',
        answer='Помощь',
        parse_mode=ParseMode.MARKDOWN_V2
    )

    help_auth = ButtonText(
        help + '\n\nЧтобы использовать бота, тебе надо авторизоваться, отправив команду /start',
        parse_mode=ParseMode.MARKDOWN_V2
    )

    support = ButtonText(
        'Напиши свой вопрос. Оператор ответит, как только освободится.'
    )
    about_us = ButtonText(
        '{} - телеграм-бот компании ООО "Айроннет" 2022\n\nДля связи с тех. поддержкой звоните по тел. '
        '8-800-222-46-69'
    )

    payments = ButtonText(
        'Платежи\n\nКак хочешь пополнить счёт?',
        answer='Платежи'
    )
    payments_promise = ButtonText(
        'Платежи >> Обещанный платёж\n\nВыбери, счёт какого договора пополнить.',
        answer='Обещанный платёж'
    )
    payments_promise_offer = ButtonText(
        'Платежи >> Обещанный платёж\n\nПодключить обещанный платёж на 100 руб. к договору №{agrm}? Его нужно будет '
        'погасить за 5 дней.',
        answer='Выбран договор {agrm}'
    )
    payments_promise_success = ButtonText(
        'Успех! Обещанный платёж успешно подключен! :tada:',
        answer='Обещанный платёж успешно подключен!'
    )
    payments_promise_fail = ButtonText(
        'Ошибка! Не удалось подключить обещанный платёж. Попробуй еще раз или обратитесь в тех.поддержку.',
        answer='Не удалось подключить обещанный платёж.'
    )
    payments_promise_already_have = ButtonText(
        'На договоре №{agrm} уже подключен обещанный платёж. Погаси долг, чтобы взять следующий обещанный платёж.',
        answer='Уже подключен на договоре №{agrm}'
    )

    payments_online = ButtonText(
        'Платежи >> Оплата Онлайн\n\nВыбери, счёт какого договора пополнить.',
        answer='Оплата Онлайн'
    )
    payments_online_amount = ButtonText(
        'Платежи >> Оплата Онлайн\n\nДоговор №{agrm}\nНа сколько хочешь пополнить счёт?\n\nВведи сумму (минимальная '
        'сумма платежа - 100 руб.)',
        answer=payments_promise_offer.answer
    )
    payments_online_amount_is_not_digit = ButtonText(
        'Платежи >> Оплата Онлайн\n\nЭто число? :thinking_face: Введи сумму, на которую хочешь пополнить счёт.'
    )
    payments_online_amount_is_too_small = ButtonText(
        'Платежи >> Оплата онлайн\n\nМинимальная сумма платежа 100 рублей.'
    )
    payments_online_offer = ButtonText(
        'Платежи >> Оплата онлайн >> Договор №{agrm}\n\nК зачислению: {amount} руб.\n'
        'Комиссия (до 4%): {tax} руб.\n\nИтого к оплате: <u>{res} руб.</u>',
        parse_mode=ParseMode.HTML
    )
    payments_online_success = ButtonText(
        'Оплата успешно прошла! Деньги на счёт поступят в ближайшие пару минут!'
    )
    payments_online_success_short = ButtonText(
        'Оплата успешно прошла!'
    )
    payments_online_fail = ButtonText(
        'Не удалось провести платёж.'
    )
    payments_online_already_have = ButtonText(
        'Этот счёт уже был оплачен.'
    )
    payments_online_already_canceled = ButtonText(
        'Этот счёт был отменён.'
    )
    payments_online_already_processing = ButtonText(
        'Подождите, этот счёт уже обрабатывается.'
    )
    payment_item_price = ButtonText(
        'Услуги доступа к сети Интернет по договору №{agrm}'
    )
    payment_item_tax = ButtonText(
        'Комиссия (до 4%)'
    )
    payment_title = ButtonText(
        'Пополнение счёта договора'
    )
    payment_description = ButtonText(
        'Пополнить счёт договора №{agrm} на {amount} руб.'
    )
    payment_description_item = ButtonText(
        'Телекоммуникационные услуги связи по договору №{agrm}'
    )
    payment_error_message = ButtonText(
        'Попробуй провести платёж ещё раз.'
    )
    payments_on_process = ButtonText(
        'Платёж обрабатывается.'
    )
    payments_online_was_paid = ButtonText(
        'Твой счёт на {amount} руб. только что оплатили :star-struck: Скоро средства поступят на твой баланс!'
    )
    payments_after_for_guest = ButtonText(
        'Ты можешь авторизоваться!\nДля этого отправь мне /start\nЧтобы узнать, что я умею отправь /help'
    )

    backend_error = ButtonText(
        'Непредвиденная ошибка!'
    )

    new_feedback = ButtonText(
        'Ты поможешь стать нам лучше, если оценишь работу наших сотрудников (от 1 до 5), выполнивших твою заявку!'
    )
    best_feedback = ButtonText(
        'Спасибо! Мы очень стараемся! :blush:',
        answer='Превосходно! 5 из 5! :party:'
    )
    why_feedback = ButtonText(
        'Можешь написать, чего не хватило до пятёрки?',
        answer='Что не так? :disappointed:'
    )
    got_feedback = ButtonText(
        'Обязательно передам это моим руководителям! Спасибо, что уделил время :relaxed: Ты помогаешь нам стать лучше!'
    )
    end_feedback_answer = \
        'Спасибо за оценку!'

    @staticmethod
    def get_account_agrm_list(data: dict):
        text = []
        for account, agrms in data.items():
            text += [f'Учетная запись: {account}\n']
            text[-1] += f'Договор: №{agrms[0]}' if len(agrms) == 1 else \
                'Договоры:\n' + '\n'.join([f' - №{agrm}' for agrm in agrms])
        return '\n\n'.join(text)
