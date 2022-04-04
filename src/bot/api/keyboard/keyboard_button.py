from aiogram import types
from aiogram.utils.emoji import emojize


class KeyboardButton:

    def __init__(
            self,
            text: str,
            **button_parameters
    ):
        self.parameters = {'text': emojize(text), **button_parameters}

    def __str__(self):
        return {**self.parameters}.__str__()

    def __getitem__(self, item: str):
        if item in self.parameters:
            return self.parameters[item]
        else:
            raise KeyError(f'{item=} given but there is {list(self.parameters.keys())}')

    def __setitem__(self, key: str, value):
        self.parameters[key] = value

    def get_button(self, keyboard_type: str):
        if keyboard_type == 'reply':
            return types.KeyboardButton(**self.parameters)
        elif keyboard_type == 'inline':
            return types.InlineKeyboardButton(**self.parameters)
