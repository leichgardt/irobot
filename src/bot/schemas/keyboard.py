from typing import List, Optional, Union

from aiogram import types

from .keyboard_button import KeyboardButton

__all__ = ('Keyboard', 'KeyboardButton')


class Keyboard:

    def __init__(
            self,
            buttons: Union[List[KeyboardButton],
                           List[Union[KeyboardButton, List[KeyboardButton]]]],
            row_size: int = 2
    ):
        self.buttons = buttons
        self.row_size = row_size

    def _fill_keyboard_with_buttons(
            self,
            keyboard: Union[types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup],
            keyboard_type: str
    ) -> Union[types.ReplyKeyboardMarkup, types.InlineKeyboardMarkup]:
        if self._is_simple_list_of_buttons():
            keyboard.add(*[button.get_button(keyboard_type) for button in self.buttons])
        else:
            for line in self.buttons:
                if isinstance(line, KeyboardButton):
                    keyboard.row(line.get_button(keyboard_type))
                else:
                    keyboard.row(*[button.get_button(keyboard_type) for button in line])
        return keyboard

    def _is_simple_list_of_buttons(self):
        return len([line for line in self.buttons if isinstance(line, list)]) == 0

    def inline(self) -> types.InlineKeyboardMarkup:
        kb = types.InlineKeyboardMarkup(row_width=self.row_size)
        kb = self._fill_keyboard_with_buttons(kb, 'inline')
        return kb

    def reply(self, *, one_time_keyboard: Optional[bool] = None) -> types.ReplyKeyboardMarkup:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=self.row_size,
                                       one_time_keyboard=one_time_keyboard)
        kb = self._fill_keyboard_with_buttons(kb, 'reply')
        return kb
