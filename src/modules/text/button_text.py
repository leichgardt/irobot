from typing import Union

from aiogram.types import ParseMode
from aiogram.utils.emoji import emojize

from src.utils import map_format


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
