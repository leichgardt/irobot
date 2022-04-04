from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.bot import keyboards
from src.bot.api import (
    get_agrm_balances,
    finish_review,
    edit_inline_message,
    delete_message,
    update_inline_query,
    private_and_login_require,
    exc_handler,
    Keyboard
)
from src.sql import sql
from src.text import Texts
from src.utils import logger
from .l2_settings import bot, dp


class ReviewFSM(StatesGroup):
    rating = State()
    comment = State()


# _______________ Помощь _______________

@dp.message_handler(Text('⛑ Помощь', ignore_case=True), state='*')
@dp.message_handler(commands='help', state='*')
@private_and_login_require(do_not_check_sub=True)
@exc_handler
async def help_message_h(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, 'typing')
    if await sql.get_sub(message.chat.id):
        kb = keyboards.help_kb
        res = await bot.send_message(message.chat.id, *Texts.help.pair(), reply_markup=kb)
        await sql.upd_inline_message(message.chat.id, res.message_id, *Texts.help.pair())
    else:
        await bot.send_message(message.chat.id, *Texts.help_auth.pair())


@dp.callback_query_handler(text='about')
@exc_handler
async def about_inline_h(query: types.CallbackQuery):
    kb = keyboards.help_kb
    await update_inline_query(query, *Texts.about_us.full(), reply_markup=kb)


@dp.callback_query_handler(text='cancel')
@exc_handler
async def inline_h_payments_choice(query: types.CallbackQuery):
    await update_inline_query(query, *Texts.cancel.full(), reply_markup=keyboards.main_menu_kb)


@dp.callback_query_handler(text='cancel', state=[ReviewFSM.rating, ReviewFSM.comment])
@dp.callback_query_handler(text='main-menu', state='*')
@exc_handler
async def main_inline_h(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await delete_message(query.message)
    await query.answer(Texts.cancel.answer)
    await bot.send_message(query.message.chat.id, *Texts.main_menu.pair(), reply_markup=keyboards.main_menu_kb)
    await sql.upd_inline_message(query.message.chat.id, 0, '')


# _______________ Баланс _______________

@dp.message_handler(commands='balance', state='*')
@dp.message_handler(Text(emojize(':scales: Баланс'), ignore_case=True), state='*')
@dp.async_task
@private_and_login_require()
@exc_handler
async def help_message_h(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, 'typing')
    text, parse_mode = await get_agrm_balances(message.chat.id)
    await bot.send_message(message.chat.id, text, parse_mode, reply_markup=keyboards.main_menu_kb)


# _______________ Отзыв _______________

@dp.message_handler(Text('💩 Оставить отзыв', ignore_case=True), state='*')
@private_and_login_require()
@exc_handler
async def review_start_inline_h(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, 'typing')
    await state.finish()
    kb = Keyboard([keyboards.get_review_btn(), keyboards.back_to_main], row_size=5).inline()
    await ReviewFSM.rating.set()
    res = await bot.send_message(message.chat.id, *Texts.review.pair(), reply_markup=kb)
    await sql.upd_inline_message(message.chat.id, res.message_id, *Texts.review.pair())
    await logger.info(f'Start review [{message.chat.id}]')


@dp.callback_query_handler(Regexp(regexp=r'review-([^\s]*)'), state=[ReviewFSM.rating, ReviewFSM.comment])
@exc_handler
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        rating = int(query.data[-1])
        if 'rating' in data.keys() and data['rating'] == rating:
            data['rating'] = 0
        else:
            data['rating'] = rating
        if 'comment' in data.keys():
            if data['rating']:
                await finish_review(query.message.chat.id, state, data['comment'], rating)
                await query.answer(Texts.review_done.answer)
                return
            else:
                kb = Keyboard([keyboards.get_review_btn(data['rating']), keyboards.review_btn], row_size=5).inline()
                text, parse_mode = Texts.review_full.pair(comment=data['comment'], rating=data['rating'])
        else:
            kb = Keyboard([keyboards.get_review_btn(data['rating']), keyboards.cancel_btn], row_size=5).inline()
            text, parse_mode = Texts.review_rate.pair(rating=data['rating'])
        await edit_inline_message(query.message.chat.id, text, parse_mode, reply_markup=kb)
        await query.answer(Texts.review_rate.answer.format(rating=data['rating']))


@dp.message_handler(state=[ReviewFSM.rating, ReviewFSM.comment])
@exc_handler
async def review_comment_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comment'] = message.text
        rating = data['rating'] if 'rating' in data.keys() else 0
        await delete_message(message)
        if rating:
            await finish_review(message.chat.id, state, data['comment'], rating)
        else:
            text, parse_mode = Texts.review_with_comment.pair(comment=data['comment'])
            kb = Keyboard([keyboards.get_review_btn(rating), keyboards.review_btn], row_size=5).inline()
            await edit_inline_message(message.chat.id, text, parse_mode, reply_markup=kb)


@dp.callback_query_handler(text='send-review', state=[ReviewFSM.rating, ReviewFSM.comment])
@exc_handler
async def review_finish_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await logger.info(f'New review [{query.message.chat.id}]')
        rating = data.get('rating')
        comment = data.get('comment')
        await query.answer(Texts.review_done.answer)
        await finish_review(query.message.chat.id, state, comment, rating)
        await sql.add_feedback(query.message.chat.id, 'review', rating=rating, comment=comment)
        await sql.upd_inline_message(query.message.chat.id, 0, '')
