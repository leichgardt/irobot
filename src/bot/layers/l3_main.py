import hashlib
import asyncio

from datetime import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, StateFilter, RegexpCommandsFilter, Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.emoji import emojize

from src.utils import logger
from src.sql import sql
from src.bot.api import main_menu, clear_inline_message, get_keyboard_menu, update_inline_query, get_agrm_balances, edit_inline_message
from .l2_settings import bot, dp


@dp.message_handler(commands='help', state='*')
async def message_h_settings(message: types.Message, state: FSMContext):
    await state.finish()
    text, kb, parse = await get_keyboard_menu('help')
    if not await sql.get_sub(message.chat.id):
        kb = None
        text += '\n\nЧтобы использовать бота, тебе надо авторизоваться, отправив команду /start'
    await clear_inline_message(bot, message.chat.id)
    res = await bot.send_message(message.chat.id, text, parse_mode=parse, reply_markup=kb)
    await sql.upd_inline(message.chat.id, res.message_id, text, parse)


@dp.callback_query_handler(text='help')
async def help_cmd_handler(query: types.CallbackQuery):
    await update_inline_query(bot, query, 'Помощь', 'help')


@dp.callback_query_handler(text='about')
async def help_cmd_handler(query: types.CallbackQuery):
    await query.answer('@ironnet_bot - телеграм-бот, разработанный ООО "Айроннет" 2021', show_alert=True)


@dp.callback_query_handler(text='main-menu', state='*')
async def inline_cb_h_main(query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await query.answer('Главное меню')
    res = await query.message.edit_text(main_menu[0], reply_markup=main_menu[1], parse_mode=main_menu[2])
    await sql.upd_inline(query.message.chat.id, res.message_id, res.text)


@dp.callback_query_handler(text='balance')
async def inline_cb_h_balance(query: types.CallbackQuery):
    logger.info(f'Balance check [{query.message.chat.id}]')
    text = f'{main_menu[0]}\n\n' + await get_agrm_balances(query.message.chat.id)
    await query.answer('Баланс')
    await edit_inline_message(bot, query.message.chat.id, text, reply_markup=main_menu[1])


class ReviewFSM(StatesGroup):
    rating = State()
    comment = State()


@dp.callback_query_handler(text='review')
async def inline_cb_h_balance(query: types.CallbackQuery):
    logger.info(f'Start review [{query.message.chat.id}]')
    smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
    btn = [types.InlineKeyboardButton(text=emojize(smile), callback_data=f'rev-{i + 1}') for i, smile in enumerate(smiles)]
    kb = types.InlineKeyboardMarkup().row(*btn).row(types.InlineKeyboardButton(text='Отмена', callback_data=f'cancel'))
    text = 'Отзыв\n\nНа сколько звёзд от 1 до 5 меня оценишь? Если хочешь, можешь не оценивать, просто напиши, что ' \
           'обо мне думаешь.'
    await ReviewFSM.rating.set()
    await edit_inline_message(bot, query.message.chat.id, text, reply_markup=kb)


@dp.callback_query_handler(Regexp(regexp=r'rev-([^\s]*)'), state=ReviewFSM.rating)
@dp.callback_query_handler(Regexp(regexp=r'rev-([^\s]*)'), state=ReviewFSM.comment)
async def inline_cb_h_balance(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['rating'] = int(query.data.replace('rev-', ''))
        await query.answer(f'Оценил на {data["rating"]}')
        smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
        smiles[data['rating'] - 1] = f'>{smiles[data["rating"] - 1]}<'
        btn = [types.InlineKeyboardButton(text=f'{emojize(smile)}', callback_data=f'rev-{i + 1}') for i, smile in
               enumerate(smiles)]
        kb = types.InlineKeyboardMarkup().row(*btn)
        btn = [types.InlineKeyboardButton(text='Отправить', callback_data=f'send-review'),
               types.InlineKeyboardButton(text='Отмена', callback_data=f'main-menu')]
        kb.row(*btn)
        if 'comment' in data.keys():
            text = f'Отзыв:\n{data["comment"]}\n\nНапиши новое сообщение, чтобы изменить отзыв, или отправь этот.'
        else:
            text = 'Напиши отзыв или отправь свою оценку.'
        await edit_inline_message(bot, query.message.chat.id, text, reply_markup=kb)


@dp.message_handler(state=ReviewFSM.rating)
@dp.message_handler(state=ReviewFSM.comment)
async def message_h_review(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comment'] = message.text
        smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
        if 'rating' in data.keys():
            smiles[data['rating'] - 1] = f'>{smiles[data["rating"] - 1]}<'
        btn = [types.InlineKeyboardButton(text=f'{emojize(smile)}', callback_data=f'rev-{i + 1}') for i, smile in
               enumerate(smiles)]
        kb = types.InlineKeyboardMarkup().row(*btn)
        btn = [types.InlineKeyboardButton(text='Отправить', callback_data=f'send-review'),
               types.InlineKeyboardButton(text='Отмена', callback_data=f'main-menu')]
        kb.row(*btn)
        breakline = '=' * 24
        text = f'Отзыв\n\n{breakline}\n{data["comment"]}\n{breakline}\n\nНапиши новое сообщение, чтобы изменить свой ' \
               f'отзыв, или отправь его.'
        await message.delete()
        await edit_inline_message(bot, message.chat.id, text, reply_markup=kb)


@dp.callback_query_handler(text='send-review', state=ReviewFSM.rating)
@dp.callback_query_handler(text='send-review', state=ReviewFSM.comment)
async def inline_cb_h_balance(query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        logger.info(f'New review saved [{query.message.chat.id}]')
        await sql.add_review(query.message.chat.id, data['rating'], data['comment'])
        await state.finish()
        text, kb, parse = await get_keyboard_menu('main', query.message.chat.id)
        text = 'Отзыв успешно отправлен! Огромное спасибо! Мы обязательно учтём твое мнение :blush:\n\n' + text
        await edit_inline_message(bot, query.message.chat.id, emojize(text), reply_markup=kb, parse_mode=parse)

