from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.utils import alogger
from src.sql import sql
from src.bot.api import main_menu, get_agrm_balances, edit_inline_message, get_keyboard, delete_message,\
    update_inline_query, private_and_login_require, run_cmd
from src.bot import keyboards
from src.text import Texts
from .l2_settings import bot, dp


class ReviewFSM(StatesGroup):
    rating = State()
    comment = State()


# _______________ Помощь _______________

@dp.message_handler(Text('⛑ Помощь', ignore_case=True), state='*')
@dp.message_handler(commands='help', state='*')
@private_and_login_require(do_not_check_sub=True)
async def help_message_h(message: types.Message, state: FSMContext):
    await run_cmd(bot.send_chat_action(message.chat.id, 'typing'))
    if await sql.get_sub(message.chat.id):
        kb = get_keyboard(keyboards.help_btn, keyboard_type='inline', lining=True)
        res = await run_cmd(bot.send_message(message.chat.id, *Texts.help.pair(), reply_markup=kb))
        await sql.upd_inline(message.chat.id, res.message_id, *Texts.help.pair())
    else:
        await run_cmd(bot.send_message(message.chat.id, *Texts.help_auth.pair()))


@dp.callback_query_handler(text='about')
async def about_inline_h(query: types.CallbackQuery):
    kb = get_keyboard(keyboards.help_btn, keyboard_type='inline', lining=True)
    await update_inline_query(query, *Texts.about_us.full(), reply_markup=kb)


@dp.callback_query_handler(text='cancel')
async def inline_h_payments_choice(query: types.CallbackQuery):
    await update_inline_query(query, *Texts.cancel.full(), reply_markup=main_menu)


@dp.callback_query_handler(text='cancel', state=[ReviewFSM.rating, ReviewFSM.comment])
@dp.callback_query_handler(text='main-menu', state='*')
async def main_inline_h(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await delete_message(query.message)
    await query.answer(Texts.cancel.answer)
    await run_cmd(bot.send_message(query.message.chat.id, *Texts.main_menu.pair(), reply_markup=main_menu))
    await sql.upd_inline(query.message.chat.id, 0, '')


# _______________ Баланс _______________

@dp.message_handler(commands='balance', state='*')
@dp.message_handler(Text(emojize(':scales: Баланс'), ignore_case=True), state='*')
@dp.async_task
@private_and_login_require()
async def help_message_h(message: types.Message, state: FSMContext):
    await run_cmd(bot.send_chat_action(message.chat.id, 'typing'))
    text = await get_agrm_balances(message.chat.id)
    await run_cmd(bot.send_message(message.chat.id, text, Texts.balance.parse_mode, reply_markup=main_menu))


# _______________ Отзыв _______________

@dp.message_handler(Text('💩 Оставить отзыв', ignore_case=True), state='*')
@private_and_login_require()
async def review_inline_h(message: types.Message, state: FSMContext):
    await run_cmd(bot.send_chat_action(message.chat.id, 'typing'))
    await state.finish()
    kb = get_keyboard(keyboards.get_review_btn(), keyboards.back_to_main, keyboard_type='inline', row_size=5)
    await ReviewFSM.rating.set()
    res = await run_cmd(bot.send_message(message.chat.id, *Texts.review.pair(), reply_markup=kb))
    await sql.upd_inline(message.chat.id, res.message_id, *Texts.review.pair())
    await alogger.info(f'Start review [{message.chat.id}]')


@dp.callback_query_handler(Regexp(regexp=r'review-([^\s]*)'), state=[ReviewFSM.rating, ReviewFSM.comment])
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['rating'] = int(query.data[-1])
        kb = get_keyboard(keyboards.get_review_btn(data['rating']), keyboards.review_btn, keyboard_type='inline', row_size=5)
        if 'comment' in data.keys():
            text, parse = Texts.review_full.pair(comment=data['comment'], rating=data['rating'])
        else:
            text, parse = Texts.review_rate.pair(rating=data['rating'])
        await edit_inline_message(query.message.chat.id, text, parse, reply_markup=kb)
        await query.answer(Texts.review_rate.answer.format(rating=data['rating']))


@dp.message_handler(state=[ReviewFSM.rating, ReviewFSM.comment])
async def review_comment_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comment'] = message.text
        rating = data['rating'] if 'rating' in data.keys() else 0
        kb = get_keyboard(keyboards.get_review_btn(rating), keyboards.review_btn, keyboard_type='inline', row_size=5)
        if rating:
            text, parse = Texts.review_full.pair(comment=data['comment'], rating=data['rating'])
        else:
            text, parse = Texts.review_with_comment.pair(comment=data['comment'])
        await delete_message(message)
        await edit_inline_message(message.chat.id, text, parse, reply_markup=kb)


@dp.callback_query_handler(text='send-review', state=[ReviewFSM.rating, ReviewFSM.comment])
async def review_send_inline_h(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        rating = data['rating'] if 'rating' in data.keys() else None
        comment = data['comment'] if 'comment' in data.keys() else None
        await sql.add_review(query.message.chat.id, rating, comment)
        if rating and comment:
            text, parse = Texts.review_result_full.pair(comment=data['comment'], rating=data['rating'])
        elif rating and not comment:
            text, parse = Texts.review_result_rate.pair(rating=data['rating'])
        else:
            text, parse = Texts.review_result_comment.pair(comment=data['comment'])
        await edit_inline_message(query.message.chat.id, text, parse)
        await query.answer(Texts.review_done.answer)
        if rating and rating == 5:
            text, parse = Texts.review_done_best.pair()
        else:
            text, parse = Texts.review_done.pair()
        await run_cmd(bot.send_message(query.message.chat.id, text, parse, reply_markup=main_menu))
        await state.finish()
        await sql.upd_inline(query.message.chat.id, 0, '')
        await alogger.info(f'New review saved [{query.message.chat.id}]')
