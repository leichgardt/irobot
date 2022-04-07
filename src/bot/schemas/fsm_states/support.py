from aiogram.dispatcher.filters.state import State, StatesGroup

__all__ = 'SupportFSM',


class SupportFSM(StatesGroup):
    # Техподдержка
    support = State()
