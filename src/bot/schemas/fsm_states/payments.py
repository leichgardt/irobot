from aiogram.dispatcher.filters.state import State, StatesGroup

__all__ = 'PaymentFSM',


class PaymentFSM(StatesGroup):
    # доп. данные
    hash = State()
    agrm_data = State()
    # этапы
    operation = State()
    agrm = State()
    amount = State()
    payment = State()
