from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize


BOT_NAME = '@ironnet_bot'


class T(str):
    def __init__(self,
                 value='',
                 parse_mode: str = None,
                 answer: str = None):
        # super(T, self).__init__()
        self.__str__ = value
        self.answer = answer
        self.parse_mode = parse_mode
    
    def full(self):
        return self.answer, self.__str__, self.parse_mode


class Texts:
    start = T(
        'Привет, {name}!\nС помощью этого бота ты сможешь проверять и пополнять баланс, менять тарифы и ещё многое '
        'другое!\nНо сначала давай авторизуемся!\n\n<u>Напиши номер договора</u>.')
    start.parse_mode = ParseMode.HTML
    cancel = T(
        'Отменено.')
    cancel.answer = \
        'Отмена'

    auth_pwd = T(emojize(
        'Договор: {agrm}\n<u>Введи пароль</u>. Не волнуйся, сообщение сразу же удалится из истории чата :sunglasses:'))
    auth_pwd.parse_mode = ParseMode.HTML
    auth_success = T(emojize(
        'Ты успешно авторизовался под договором {agrm} :tada:\nДобро пожаловать! :smile:'))
    auth_fail = T(
        'Неправильный номер договора или пароль. Попробуй еще раз!\n\nВведи номер договора.')
    auth_error = T(
        'Ошибка! Договор не найден.\nПопробуй ввести номер другого договора.')
    auth_cancel = T(
        'Отменено. Отправь /start чтобы начать.')
    auth_cancel.answer = \
        'Начало'

    settings = T(
        'Настройки\n\nВыбери пункт настроек.')
    settings_non_auth = T(
        'Чтобы настраивать бота, тебе надо авторизоваться, отправив команду /start')
    settings_done = T(
        'Настройки сохранены.')
    settings_done.answer = \
        'Настройки сохранены'
    settings_agrms = T(
        'Настройки >> Договоры\n\nДобавь ещё договор или удали добавленные.')
    settings_agrms.answer = \
        'Настройки договоров'
    settings_agrm = T(emojize(
        'Настройки >> Договоры >> №{agrm}\n\nУдалять не обязательно, можно просто отключить уведомления в настройках '
        'уведомлений :wink:\nНо удалив договор, ты не сможешь проверять баланс, и мы не сможем предупредить тебя, если '
        'деньги будут заканчиваться! :scream:'))
    settings_agrm.answer = \
        'Настройки договора №{agrm}'
    settings_agrm_del_answer = T(
        'Договор {agrm} удалён')
    settings_agrm_add = T(
        'Настройки >> Договоры >> Добавить\n\nВведи номер договора.')
    settings_agrm_add.answer = \
        'Добавить новый договор'
    settings_agrm_pwd = T(emojize(
        'Настройки >> Договоры >> Добавить\n\nНомер договора: {agrm} \nВведи пароль.'))
    settings_agrm_add_success = T(emojize(
        'Настройки >> Договоры\n\nДоговор {agrm} успешно добавлен :tada:\nДобавь еще договор или удали '
        'добавленные'))
    settings_agrm_exist = T(
        'Настройки >> Договоры\n\nДоговор №{agrm} уже добавлен.\nВведи <u>другой</u> договор.')
    settings_agrm_exist.parse_mode = ParseMode.HTML
    settings_agrm_add_fail = auth_fail
    settings_agrm_add_error = auth_error
    settings_notify = T(emojize(
        'Настройки >> Уведомления\n\nМы будем уведомлять тебя, если что-то произойдёт. Например, заранее сообщим о '
        'работах, когда интернет будет недоступен!\nОтключи уведомления, если они тебе мешают, но из-за этого нам будет'
        ' очень грустно :disappointed:\n\nВ новостных рассылках мы будем рассказывать тебе об акциях, скидках и о '
        'других интересных вещах, которые происходят у нас в Айроннет! :blush:'))
    settings_notify.answer = \
        'Настройки уведомлений'
    settings_notify_switch_answer = T(
        'Уведомления переключены')
    settings_mailing_switch_answer = T(
        'Новости переключены')
    settings_exit = T(emojize(
        'Уверен, что хочешь выйти? :cry:\n Все твои договоры будут отключены от Бота'))
    settings_exit.answer = \
        'Выйти?'
    settings_exited = T(emojize(
        'Ты успешно вышел. Возвращайся по-скорее! :smile:\nОтправь /start чтобы начать.'))
    settings_exited.answer = \
        'Успешный выход'

    main_menu = T(
        f'{BOT_NAME} Главное меню')
    main_menu.answer = \
        'Главное меню'

    balance = T(
        'Баланс договора №{agrm}:\n{summ} руб.\n')
    balance.answer = \
        'Баланс'
    balance_credit = T(
        'Обещанный платёж:\n{cre} руб. до {date}\n')
    balance_no_agrms = T(
        'У тебя удалены все договоры. Добавь их в Настройках Договоров /settings')

    review = T(
        'Отзыв\n\nНа сколько звёзд от 1 до 5 меня оценишь? Или можешь просто написать, что обо мне думаешь.')
    review.answer = \
        'Отзыв'
    review_rate = T(
        'Отзыв\n\nОценка: {rating}\nНапиши отзыв или отправь оценку.')
    review_rate.answer = \
        'Оценил на {rating}!'
    review_with_comment = T(
        'Отзыв:\n' + '_' * 40 + '\n{comment}\n' + '_' * 40 + '\n\nНапиши новое сообщение, чтобы изменить свой отзыв, '
        'или отправь это.')
    review_full = T(
        'Отзыв:\n' + '_' * 40 + '\n{comment}\n' + '_' * 40 + '\nОценка: {rating}\n\nНапиши новое сообщение, чтобы'
        ' изменить свой отзыв, или отправь это.')
    review_done = T(emojize(
        'Отзыв успешно отправлен! Спасибо огромное! Мы обязательно учтём твое мнение :blush:'))
    review_done.answer = \
        'Отзыв отправлен'

    help = T(
        'Помощь\n\nС помощью этого бота ты можешь\:\n\- проверять свой __баланс__\n\- __пополнять__ счёт\n\- менять '
        '__тариф__\n\- добавить несколько учётных записей через __настройки__\n\- и следить за всеми добавленными '
        'договорами\n\n*Команды*\n/start \- начать работу\n/help \- увидеть это сообщение\n/settings \- настроить бота')
    help.parse_mode = ParseMode.MARKDOWN_V2
    help.answer = \
        'Помощь'
    help_auth = T(
        help + '\n\nЧтобы использовать бота, тебе надо авторизоваться, отправив команду /start')
    help_auth.parse_mode = ParseMode.MARKDOWN_V2

    about_answer = T('@ironnet_bot - телеграм-бот, разработанный ООО "Айроннет" 2021')

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
    payments_already_have = T(
        'На договоре №{agrm} уже подключен обещанный платёж. Погаси долг, чтобы взять следующий обещанный платёж.')
    payments_already_have.answer = \
        'Уже подключен на договоре №{agrm}'

    payments_online = T(
        'Платежи >> Оплата Онлайн\n\nВыбери, счёт какого договора пополнить.')
    payments_online.answer = \
        'Оплата Онлайн'
    payments_online_amount = T(
        'Платежи >> Оплата Онлайн\n\nДоговор №{agrm}\n\nНа сколько хочешь пополнить счёт?\n\nВведи сумму.')
    payments_online_amount.answer = payments_promise_offer.answer
    payments_online_amount_is_not_digit = T(
        'Платежи >> Оплата Онлайн\n\nНе могу понять, что ты написал. Введи число.')
    payments_online_offer = T(
        'Платежи >> Оплата онлайн\n\nДоговор №{agrm}\n\nК оплате: {amount} руб.\nКомиссия: {tax} руб.\n\n'
        'Итого к зачислению: {res} руб.\n\nНажми на кнопку "Оплатить", чтобы перейти к оплате, или введи другую сумму.')
