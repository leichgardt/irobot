from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, get_agrm_balances, edit_inline_message, get_keyboard, delete_message,\
    update_inline_query, private_and_login_require
from src.bot import keyboards
from src.bot.text import Texts
from .l2_settings import bot, dp


class ReviewFSM(StatesGroup):
    rating = State()
    comment = State()


@dp.message_handler(Text('⛑ Помощь', ignore_case=True), state='*')
@dp.message_handler(commands='help', state='*')
@private_and_login_require(do_not_check_sub=True)
async def help_message_h(message: types.Message, state: FSMContext):
    if await sql.get_sub(message.chat.id):
        kb = get_keyboard(keyboards.help_btn, keyboard_type='inline', lining=True)
        res = await bot.send_message(message.chat.id, Texts.help, parse_mode=Texts.help.parse_mode, reply_markup=kb)
        await sql.upd_inline(message.chat.id, res.message_id, res.text, Texts.help.parse_mode)
    else:
        await bot.send_message(message.chat.id, Texts.help_auth, parse_mode=Texts.help_auth.parse_mode)


@dp.callback_query_handler(text='about')
async def about_inline_h(query: types.CallbackQuery):
    await query.answer(Texts.about_answer, show_alert=True)


@dp.callback_query_handler(text='cancel')
async def inline_h_payments_choice(query: types.CallbackQuery):
    await update_inline_query(bot, query, *Texts.cancel.full())
    await bot.send_message(query.message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode, reply_markup=main_menu)


@dp.callback_query_handler(text='cancel', state=[ReviewFSM.rating, ReviewFSM.comment])
@dp.callback_query_handler(text='main-menu', state='*')
async def main_inline_h(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await delete_message(query.message)
    await bot.send_message(query.message.chat.id, Texts.main_menu, Texts.main_menu.parse_mode, reply_markup=main_menu)
    await query.answer(Texts.cancel.answer)
    await sql.upd_inline(query.message.chat.id, 0, '')


@dp.message_handler(Text(emojize(':scales: Баланс'), ignore_case=True), state='*')
@dp.async_task
@private_and_login_require()
async def help_message_h(message: types.Message, state: FSMContext):
    await bot.send_chat_action(message.chat.id, 'typing')
    text = await get_agrm_balances(message.chat.id)
    await bot.send_message(message.chat.id, text, reply_markup=main_menu)


@dp.message_handler(Text('💩 Оставить отзыв', ignore_case=True), state='*')
@private_and_login_require()
async def review_inline_h(message: types.Message, state: FSMContext):
    await state.finish()
    kb = get_keyboard(keyboards.get_review_btn(), keyboards.cancel_btn, keyboard_type='inline', row_size=5)
    await ReviewFSM.rating.set()
    res = await bot.send_message(message.chat.id, Texts.review, Texts.review.parse_mode, reply_markup=kb)
    await sql.upd_inline(message.chat.id, res.message_id, res.text, Texts.review.parse_mode)
    await alogger.info(f'Start review [{message.chat.id}]')


@dp.callback_query_handler(Regexp(regexp=r'review-([^\s]*)'), state=[ReviewFSM.rating, ReviewFSM.comment])
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['rating'] = int(query.data[-1])
        kb = get_keyboard(keyboards.get_review_btn(data['rating']), keyboards.review_btn, keyboard_type='inline', row_size=5)
        if 'comment' in data.keys():
            text = Texts.review_full.format(comment=data['comment'], rating=data['rating'])
        else:
            text = Texts.review_rate.format(rating=data['rating'])
        await edit_inline_message(bot, query.message.chat.id, text, reply_markup=kb)
        await query.answer(Texts.review_rate.answer.format(rating=data['rating']))


@dp.message_handler(state=[ReviewFSM.rating, ReviewFSM.comment])
async def review_comment_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await message.delete()
        data['comment'] = message.text
        rating = data['rating'] if 'rating' in data.keys() else 0
        kb = get_keyboard(keyboards.get_review_btn(rating), keyboards.review_btn, keyboard_type='inline', row_size=5)
        if 'rating' in data.keys():
            text = Texts.review_full.format(comment=data['comment'], rating=data['rating'])
        else:
            text = Texts.review_with_comment.format(comment=data['comment'])
        await edit_inline_message(bot, message.chat.id, text, reply_markup=kb)


@dp.callback_query_handler(text='send-review', state=[ReviewFSM.rating, ReviewFSM.comment])
async def review_send_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        rating = data['rating'] if 'rating' in data.keys() else None
        comment = data['comment'] if 'comment' in data.keys() else None
        await sql.add_review(query.message.chat.id, rating, comment)
        await state.finish()
        text = query.message.text.rsplit('\n\n', 1)[0]
        await edit_inline_message(bot, query.message.chat.id, text)
        await query.answer(Texts.review_done.answer)
        await bot.send_message(query.message.chat.id, Texts.review_done, Texts.review_done.parse_mode,
                               reply_markup=main_menu)
        await alogger.info(f'New review saved [{query.message.chat.id}]')
        await sql.upd_inline(query.message.chat.id, 0, '')
