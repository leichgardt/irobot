from aiogram.dispatcher.filters.state import State, StatesGroup

__all__ = 'FeedbackFSM',


class FeedbackFSM(StatesGroup):
    message_id = State()
    task = State()
    comment = State()
    feedback_id = State()
