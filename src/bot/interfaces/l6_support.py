from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp

from src.bot.api import update_inline_query, exc_handler
from src.bot.schemas import keyboards
from src.bot.schemas.fsm_states import SupportFSM
from src.bot.utils import support
from src.modules import Texts
from src.utils import logger
from .l5_feedback import bot, dp


# _____ client side _____


@dp.callback_query_handler(text='support', state='*')
@exc_handler
async def support_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ Активация режима обращения в поддержку """
    await state.finish()
    await logger.info(f'Support enabled [{query.message.chat.id}]')
    await SupportFSM.support.set()
    await update_inline_query(query, *Texts.support.full())


@dp.message_handler(lambda message: message.text not in ['/cancel', '/end_support'],
                    state=SupportFSM.support)
@dp.message_handler(content_types=['document', 'photo', 'sticker', 'voice', 'video', 'video_note', 'audio'],
                    state=SupportFSM.support)
@exc_handler
async def support_message_h(message: types.Message, state: FSMContext):
    """ Приём текстовых сообщений в режиме поддержки"""
    async with state.proxy() as data:
        if not data.get('support'):  # если это первое сообщение
            data['support'] = await support.create_support(message.chat.id)  # создать обращение
        await support.add_support_message(message)


@dp.message_handler(commands=['end_support', 'cancel'], state=SupportFSM.support)
@exc_handler
async def cancel_support_message_h(message: types.Message, state: FSMContext):
    """ Отмена обращения """
    async with state.proxy() as data:
        await state.finish()
        await bot.send_message(message.chat.id, *Texts.cancel.pair())
        await bot.send_message(message.chat.id, *Texts.main_menu.pair(), reply_markup=keyboards.main_menu_kb)
        await support.close_support(data['support'])
        await support.add_system_support_message(message.chat.id, message.message_id, 'Абонент закрыл поддержку')


@dp.callback_query_handler(Regexp(regexp=r'support-feedback-([0-9]*)-([1-5]*)'), state='*')
@exc_handler
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ Обработка обратной связи """
    await logger.info(f'Support feedback rated [{query.message.chat.id}]')
    _, _, support_id, rating = query.data.split('-')
    await update_inline_query(query, f'Оценил на {rating}', 'Спасибо за отзыв!')
    await support.rate_support(int(support_id), int(rating))
    await support.add_system_support_message(query.message.chat.id, query.message.message_id,
                                             f'Абонент оценил поддержку на "{rating}"')
