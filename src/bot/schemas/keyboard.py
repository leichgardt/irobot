from typing import List, Optional, Union

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from .keyboard_button import KeyboardButton

__all__ = ('Keyboard', 'KeyboardButton')


class Keyboard:

    def __init__(self, buttons: Union[List[KeyboardButton],
                                      List[Union[KeyboardButton, List[KeyboardButton]]]]):
        self.buttons = buttons

    @classmethod
    def inline(
            cls,
            buttons: Union[List[KeyboardButton],
                           List[Union[KeyboardButton, List[KeyboardButton]]]],
            row_size: int = 2
    ) -> InlineKeyboardMarkup:
        self = cls(buttons)
        kb = InlineKeyboardMarkup(row_width=row_size)
        return self._fill_keyboard_with_buttons(kb, 'inline')

    @classmethod
    def reply(
            cls,
            buttons: Union[List[KeyboardButton],
                           List[Union[KeyboardButton, List[KeyboardButton]]]],
            row_size: int = 2,
            *,
            one_time_keyboard: Optional[bool] = None
    ) -> InlineKeyboardMarkup:
        self = cls(buttons)
        kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=row_size, one_time_keyboard=one_time_keyboard)
        return self._fill_keyboard_with_buttons(kb, 'reply')

    def _fill_keyboard_with_buttons(
            self,
            keyboard: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup],
            keyboard_type: str
    ) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]:
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
