from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp

from src.bot.api import update_inline_query, exc_handler
from src.bot.schemas import keyboards
from src.bot.schemas.fsm_states import SupportFSM
from src.bot.utils import support
from src.modules import sql, Texts
from src.utils import logger
from .l5_feedback import bot, dp


# _____ client side _____


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
        await support.save_dialog_message(message)
        await support.broadcast_support_message(message.chat.id, message.message_id)


@dp.message_handler(commands=['end_support', 'cancel'], state=SupportFSM.live)
@exc_handler
async def cancel_support_message_h(message: types.Message, state: FSMContext):
    """ Отмена обращения """
    await state.finish()
    await bot.send_message(message.chat.id, *Texts.cancel.pair(), reply_markup=keyboards.main_menu_kb)
    await sql.update('irobot.subs', f'chat_id={message.chat.id}', support_mode=False, inline_msg_id=0,
                     inline_text='', inline_parse_mode=None)


@dp.callback_query_handler(Regexp(regexp=r'support-feedback-([1-5]*)'), state='*')
@exc_handler
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ Обработка обратной связи """
    await logger.info(f'Support feedback rated [{query.message.chat.id}]')
    await sql.update('irobot.subs', f'chat_id={query.message.chat.id}', support_mode=False, inline_msg_id=0,
                     inline_text='', inline_parse_mode=None)
    rating = int(query.data.split('-')[2])
    await sql.add_feedback(query.message.chat.id, 'support', None, rating)
    await update_inline_query(query, f'Оценил на {rating}', 'Спасибо за отзыв!', reply_markup=keyboards.main_menu_kb)
