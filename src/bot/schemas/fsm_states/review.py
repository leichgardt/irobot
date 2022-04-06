from aiogram.dispatcher.filters.state import State, StatesGroup

__all__ = 'ReviewFSM',


class ReviewFSM(StatesGroup):
    rating = State()
    comment = State()
