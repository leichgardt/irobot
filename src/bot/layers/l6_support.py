import asyncio

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime

from src.utils import alogger
from src.sql import sql
from src.bot import keyboards
from src.bot.api import main_menu, update_inline_query, exc_handler
from src.bot.api.keyboard import Keyboard
from src.text import Texts
from .l5_feedback import bot, dp


async def save_dialog_message(message: types.Message, user: str):
    if message.content_type == 'text':
        data = {'text': message.text}
    elif message.content_type == 'document':
        data = {'file_id': message.document.file_id, 'mime_type': message.document.mime_type}
    elif message.content_type == 'photo':
        data = {'file_id': message.photo[-1].file_id}
    elif message.content_type == 'sticker':
        data = {'file_id': message.sticker.file_id}
    elif message.content_type == 'voice':
        data = {'file_id': message.voice.file_id}
    elif message.content_type == 'video':
        data = {'file_id': message.video.file_id, 'mime_type': message.video.mime_type}
    elif message.content_type == 'video_note':
        data = {'file_id': message.video_note.file_id}
    elif message.content_type == 'audio':
        data = {'file_id': message.audio.file_id, 'mime_type': message.audio.mime_type}
    else:
        await alogger.warning(f'Unhandled support message content type: {message} [{message.chat.id}]')
        return
    data = {'caption': message.caption, **data} if 'caption' in message else data
    await sql.add_support_message(message.chat.id, message.message_id, user, message.content_type, data)


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
    await alogger.info(f'Support enabled [{query.message.chat.id}]')
    await SupportFSM.live.set()
    await sql.update('irobot.subs', f'chat_id={query.message.chat.id}', support_mode=True)
    await update_inline_query(query, *Texts.support.full(), reply_markup=Keyboard(keyboards.cancel_btn).inline())


@dp.message_handler(lambda message: message.text not in ['/cancel', '/end_support'], state=SupportFSM.live)
@exc_handler
async def support_message_h(message: types.Message, state: FSMContext):
    """ Приём текстовых сообщений в режиме поддержки"""
    async with state.proxy() as data:
        if not data.get('operator'):  # если оператора нет
            if not data.get('live'):  # если это первое сообщение
                data['live'] = datetime.now().timestamp()  # сохранить время первого сообщения
                # broadcast to opers
                ops = await sql.execute('select chat_id from irobot.operators where enabled=true')
                for operator in ops:
                    await bot.send_message(
                        operator[0], f'Клиент {message.from_user.id} обратился в поддержку. Примите запрос?',
                        reply_markup=Keyboard(keyboards.get_support_kb(message.chat.id)).inline()
                    )
        else:
            await message.send_copy(data.get('operator').get('chat_id'))
        await save_dialog_message(message, 'user')


@dp.message_handler(content_types=['document', 'photo', 'sticker', 'voice', 'video', 'video_note', 'audio'],
                    state=SupportFSM.live)
@exc_handler
async def support_content_h(message: types.Message, state: FSMContext):
    """ Приём контентных сообщений в режиме поддержки """
    async with state.proxy() as data:
        if not data.get('live'):
            await bot.send_message(message.chat.id, 'Чтобы начать обращение, начни с текстового сообщения.')
            return
        else:
            await message.send_copy(data.get('operator').get('chat_id'))
            await save_dialog_message(message, 'user')
            # TODO push web-notify with new message


@dp.message_handler(commands=['end_support', 'cancel'], state=SupportFSM.live)
@exc_handler
async def cancel_support_message_h(message: types.Message, state: FSMContext):
    """ отмена обращения """
    async with state.proxy() as data:
        if data.get('operator'):
            await bot.send_message(data['operator']['chat_id'], f'Пользователь {message.chat.id} завершил поддержку.')
            await dp.storage.reset_state(chat=data['operator']['chat_id'])
    await state.finish()
    await bot.send_message(message.chat.id, *Texts.main_menu.pair(), reply_markup=main_menu)
    await sql.update('irobot.subs', f'chat_id={message.chat.id}', support_mode=False, inline_msg_id=0,
                     inline_text='', inline_parse_mode=None)


@dp.callback_query_handler(text='cancel', state=SupportFSM.live)
@exc_handler
async def cancel_support_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ отмена обращения """
    await update_inline_query(query, Texts.cancel.answer, 'Спасибо за обращение!')
    await cancel_support_message_h(query.message, state)


class SupportReviewFSM(StatesGroup):
    # Оценка техподдержки
    rating = State()
    comment = State()


@dp.callback_query_handler(Regexp(regexp=r'support-feedback-([1-5]*)'), state='*')
@exc_handler
async def review_rating_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ обработка обратной связи """
    async with state.proxy() as data:
        await alogger.info(f'Support feedback rated [{query.message.chat.id}]')
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
            await update_inline_query(query, 'Оценил на 5', 'Спасибо за хороший отзыв!', reply_markup=main_menu)


@dp.callback_query_handler(text='pass', state=SupportReviewFSM.comment)
@exc_handler
async def pass_commenting_support_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ пропустить оценку обратной связи """
    async with state.proxy() as data:
        await state.finish()
        await sql.add_feedback(query.message.chat.id, 'support', data.get('operator'), data['rating'])
        await update_inline_query(query, *Texts.passed.full())
        await bot.send_message(query.message.chat.id, *Texts.main_menu.pair(), reply_markup=main_menu)


@dp.message_handler(state=SupportReviewFSM.comment)
@exc_handler
async def review_rating_message_h(message: types.Message, state: FSMContext):
    """ обработка текста обратной связи """
    async with state.proxy() as data:
        await state.finish()
        await sql.add_feedback(message.chat.id, 'support', data['operator'], data['rating'], message.text)
        await bot.send_message(message.chat.id, 'Спасибо за отзыв!')
        await bot.send_message(message.chat.id, *Texts.main_menu.pair(), reply_markup=main_menu)


# _____ operator side _____


class OpSupportFSM(StatesGroup):
    operator = State()
    chat_id = State()


@dp.callback_query_handler(Regexp(regexp=r'get-support-line-([0-9]*)'), state='*')
@exc_handler
async def oper_take_support_inline_h(query: types.CallbackQuery, state: FSMContext):
    """ Принять линию поддержки """
    client_chat_id = int(query.data.rsplit('-', 1)[-1])
    data = await dp.storage.get_data(chat=client_chat_id)
    if data.get('operator') is not None:
        await update_inline_query(query, 'Отмена', f'Запрос уже был принят оператором {data["operator"]}')
    else:
        await state.finish()
        await OpSupportFSM.chat_id.set()
        # op = await sql.get_operator(query.message.chat.id)
        op = await sql.execute('select username from irobot.operators where chat_id=%s', query.message.chat.id)
        op = op[0][0]
        # записали оператора и чат клиента за ним
        await state.update_data(chat_id=client_chat_id, operator=op)
        # записали клиенту оператора
        await dp.storage.update_data(chat=client_chat_id, data=dict(operator=dict(name=op, chat_id=query.message.chat.id)))
        await update_inline_query(query, 'Запрос принят', 'Запрос принят. Для окончания режима поддержки отправьте '
                                                          'команду /end_support или /cancel')
        # передали историю сообщений с текущего обращения
        messages = await sql.execute('select message_id from irobot.support_dialogs where writer=%s and '
                                     'datetime + interval \'1 seconds\'>=%s',
                                     'user', datetime.fromtimestamp(data['live']))
        for msg in messages:
            await bot.copy_message(query.message.chat.id, client_chat_id, msg[0])


@dp.message_handler(commands=['end_support', 'cancel'], state=OpSupportFSM.chat_id)
@exc_handler
async def oper_cancel_support_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await dp.storage.reset_state(chat=data['chat_id'])
        await bot.send_message(message.chat.id, f'Линия поддержки с пользователем {data["chat_id"]} закрыта.')
        await asyncio.sleep(3)
        kb = Keyboard(keyboards.get_review_btn(0, 'support-feedback'), row_size=5).inline()
        await bot.send_message(data['chat_id'], 'Спасибо за обращение! Пожалуйста, оцени работу оператора',
                               reply_markup=kb)


@dp.message_handler(lambda message: message.text not in ['/cancel', '/end_support'], state=OpSupportFSM.chat_id)
@exc_handler
async def oper_support_message_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await message.send_copy(data['chat_id'])
        await save_dialog_message(message, data['operator'])


@dp.message_handler(content_types=['document', 'photo', 'sticker', 'voice', 'video', 'video_note', 'audio'],
                    state=OpSupportFSM.chat_id)
@exc_handler
async def oper_support_content_h(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        await message.send_copy(data['chat_id'])
        await save_dialog_message(message, data['operator'])
