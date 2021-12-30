from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, get_keyboard, update_inline_query, edit_inline_message, run_cmd
from src.bot import keyboards
from src.text import Texts
from .l4_payment import bot, dp


class FeedbackFSM(StatesGroup):
    message_id = State()
    task = State()
    rating = State()
    comment = State()


@dp.callback_query_handler(Regexp(regexp=r'feedback-[0-9]-([0-9]*)'), state='*')
async def feedback_inline_h(query: types.CallbackQuery, state: FSMContext):
    await alogger.info(f'Feedback [{query.message.chat.id}]')
    await state.finish()
    _, rating, task = query.data.split('-')
    rating, task = int(rating), int(task)
    if rating == 5:
        await sql.add_feedback(query.message.chat.id, 'feedback', task, rating)
        await update_inline_query(query, *Texts.best_feedback.full())
    else:
        await FeedbackFSM.comment.set()
        await state.update_data(task=task, rating=rating, message_id=query.message.message_id)
        await update_inline_query(query, *Texts.why_feedback.full(), reply_markup=get_keyboard(keyboards.pass_btn))


@dp.callback_query_handler(text='pass', state=FeedbackFSM.comment)
async def comment_feedback_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await alogger.info(f'Feedback rated and passed [{query.message.chat.id}]')
        await state.finish()
        await sql.add_feedback(query.message.chat.id, 'feedback', data['task'], data['rating'])
        await update_inline_query(query, Texts.end_feedback_answer, *Texts.main_menu.pair(), reply_markup=main_menu)


@dp.message_handler(state=FeedbackFSM.comment)
async def feedback_comment_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await alogger.info(f'Feedback commented [{message.chat.id}]')
        await state.finish()
        await sql.add_feedback(message.chat.id, 'feedback', data['task'], data['rating'], message.text)
        await bot.send_message(message.chat.id, *Texts.got_feedback.pair(), reply_markup=main_menu)
        await edit_inline_message(message.chat.id, *Texts.why_feedback.pair(), inline=data['message_id'])
