from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.bot import keyboards
from src.bot.api import update_inline_query, exc_handler, Keyboard, save_dialog_message, broadcast_support_message
from src.sql import sql
from src.text import Texts
from src.utils import logger
from .l5_feedback import bot, dp


# _____ client side _____


class SupportFSM(StatesGroup):
    # Техподдержка
    operator = State()
    live = State()


@dp.callback_query_handler(text='support', state='*')
@exc_handler
async def support_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ Активация режима обращения в поддержку """
    await state.finish()
    await logger.info(f'Support enabled [{query.message.chat.id}]')
    await SupportFSM.live.set()
    await sql.update('irobot.subs', f'chat_id={query.message.chat.id}', support_mode=True)
    await update_inline_query(query, *Texts.support.full())


@dp.message_handler(lambda message: message.text not in ['/cancel', '/end_support'],
                    state=SupportFSM.live)
@dp.message_handler(content_types=['document', 'photo', 'sticker', 'voice', 'video', 'video_note', 'audio'],
                    state=SupportFSM.live)
@exc_handler
async def support_message_h(message: types.Message, state: FSMContext):
    """ Приём текстовых сообщений в режиме поддержки"""
    async with state.proxy() as data:
        if not data.get('live'):  # если это первое сообщение
            data['live'] = datetime.now().timestamp()  # сохранить время первого сообщения
        await save_dialog_message(message)
        await broadcast_support_message(message.chat.id, message.message_id)


@dp.message_handler(commands=['end_support', 'cancel'], state=SupportFSM.live)
@exc_handler
async def cancel_support_message_h(message: types.Message, state: FSMContext):
    """ Отмена обращения """
    await state.finish()
    await bot.send_message(message.chat.id, *Texts.cancel.pair(), reply_markup=keyboards.main_menu_kb)
    await sql.update('irobot.subs', f'chat_id={message.chat.id}', support_mode=False, inline_msg_id=0,
                     inline_text='', inline_parse_mode=None)


class SupportReviewFSM(StatesGroup):
    # Оценка техподдержки
    rating = State()
    comment = State()


@dp.callback_query_handler(Regexp(regexp=r'support-feedback-([1-5]*)'), state='*')
@exc_handler
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ обработка обратной связи """
    async with state.proxy() as data:
        await logger.info(f'Support feedback rated [{query.message.chat.id}]')
        await sql.update('irobot.subs', f'chat_id={query.message.chat.id}', support_mode=False)
        rating = int(query.data.split('-')[2])
        if rating < 5:
            await state.update_data(rating=rating)
            await SupportReviewFSM.comment.set()
            await update_inline_query(
                query,
                f'Оценил на {rating}',
                'Что-то было не так? Напиши пожалуйста, мы обязательно учтём твоё мнение!',
                btn_list=[keyboards.pass_btn]
            )
        else:
            await state.finish()
            await sql.add_feedback(query.message.chat.id, 'support', data.get('operator'), rating)
            await update_inline_query(query, 'Оценил на 5', 'Спасибо за хороший отзыв!',
                                      reply_markup=keyboards.main_menu_kb)


@dp.callback_query_handler(text='pass', state=SupportReviewFSM.comment)
@exc_handler
async def pass_commenting_support_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ пропустить оценку обратной связи """
    async with state.proxy() as data:
        await state.finish()
        await sql.add_feedback(query.message.chat.id, 'support', data.get('operator'), data['rating'])
        await update_inline_query(query, *Texts.passed.full())
        await bot.send_message(query.message.chat.id, *Texts.main_menu.pair(), reply_markup=keyboards.main_menu_kb)


@dp.message_handler(state=SupportReviewFSM.comment)
@exc_handler
async def review_rating_message_h(message: types.Message, state: FSMContext):
    """ обработка текста обратной связи """
    async with state.proxy() as data:
        await state.finish()
        await sql.add_feedback(message.chat.id, 'support', data['operator'], data['rating'], message.text)
        await bot.send_message(message.chat.id, 'Спасибо за отзыв!')
        await bot.send_message(message.chat.id, *Texts.main_menu.pair(), reply_markup=keyboards.main_menu_kb)
