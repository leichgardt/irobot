from aiogram.dispatcher import FSMContext

from src.bot.api import edit_inline_message
from src.bot.core import bot
from src.bot.schemas import keyboards
from src.modules.text import Texts


async def finish_review(chat_id: int, state: FSMContext, comment: str, rating: int):
    await state.finish()
    if rating:
        text, parse_mode = Texts.review_result_full.pair(comment=comment, rating=rating)
    else:
        text, parse_mode = Texts.review_result_comment.pair(comment=comment)
    await edit_inline_message(chat_id, text, parse_mode, reply_markup=None)
    await answer_to_review(chat_id, rating)


async def answer_to_review(chat_id: int, rating: int):
    kb = keyboards.main_menu_kb
    if rating and rating == 5:
        await bot.send_message(chat_id, *Texts.review_done_best.pair(), reply_markup=kb)
    else:
        await bot.send_message(chat_id, *Texts.review_done.pair(), reply_markup=kb)
