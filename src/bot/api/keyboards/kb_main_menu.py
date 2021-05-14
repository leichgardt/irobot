from aiogram import types
from aiogram.utils.emoji import emojize

from src.sql import sql


back_to_main = (
    (
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)
main_menu_btn = (
    (
        {'text': ':scales: Баланс', 'callback_data': 'balance'},
        {'text': ':moneybag: Обещанный платёж', 'callback_data': 'payments'},
    ),
    (
        # {'text': 'Тариф', 'callback_data': 'tariff'},
        {'text': ':helmet_with_white_cross: Помощь', 'callback_data': 'help'},
        {'text': ':wrench: Настройки', 'callback_data': 'settings'},
    ),
    (
        # {'text': 'Помощь', 'callback_data': 'help'},
        {'text': '💩 Оставить отзыв', 'callback_data': 'review'},
    ),
)
help_btn = (
    (
        {'text': 'Что я умею (youtube)', 'url': 'https://www.youtube.com/watch?v=bxqLsrlakK8'},
    ),
    (
        {'text': 'О программе', 'callback_data': 'about'},
        {'text': 'Назад', 'callback_data': 'main-menu'},
    ),
)
