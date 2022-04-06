from aiogram.dispatcher.filters.state import State, StatesGroup

__all__ = 'AccountSettingsFSM',


class AccountSettingsFSM(StatesGroup):
    accounts = State()
    mailing = State()
    acc = State()
