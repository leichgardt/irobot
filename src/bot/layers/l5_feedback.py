from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, get_keyboard, update_inline_query, edit_inline_message
from src.bot import keyboards
from src.bot.text import Texts
from .l4_payment import bot, dp


class FeedbackFSM(StatesGroup):
    message_id = State()
    task = State()
    rating = State()
    comment = State()


@dp.callback_query_handler(Regexp(regexp=r'feedback-[0-9]-([0-9]*)'), state='*')
async def feedback_inline_h(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    _, rating, task = query.data.split('-')
    rating, task = int(rating), int(task)
    task = await sql.find_feedback_id(task, 'sent')
    if not task:
        await query.answer(Texts.backend_error)
        return
    if rating == 5:
        ans, txt, prs = Texts.best_feedback.full()
        kb = None
    else:
        ans, txt, prs = Texts.why_feedback.full()
        kb = get_keyboard(keyboards.pass_btn)
        await FeedbackFSM.comment.set()
        await state.update_data(task=task, rating=rating, message_id=query.message.message_id)
    await sql.upd_feedback(task, rating=rating, status='complete' if rating == 5 else 'rated')
    await query.answer(ans)
    await query.message.edit_text(txt, prs, reply_markup=kb)
    await alogger.info(f'Feedback [{query.message.chat.id}]')


@dp.callback_query_handler(text='pass', state=FeedbackFSM.comment)
async def comment_feedback_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await state.finish()
        await update_inline_query(query, Texts.end_feedback_answer, Texts.main_menu, Texts.main_menu.parse_mode,
                                  reply_markup=main_menu)
        await sql.upd_feedback(data['task'], status='complete')
        await alogger.info(f'Pass feedback [{query.message.chat.id}]')


@dp.message_handler(state=FeedbackFSM.comment)
async def feedback_comment_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await state.finish()
        await bot.send_message(message.chat.id, Texts.got_feedback, Texts.got_feedback.parse_mode, reply_markup=main_menu)
        await edit_inline_message(message.chat.id, Texts.why_feedback, Texts.why_feedback.parse_mode,
                                  inline=data['message_id'])
        await sql.upd_feedback(data['task'], comment=message.text, status='complete')
        await alogger.info(f'Comment feedback [{message.chat.id}]')
