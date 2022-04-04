from src.bot.api.keyboard import KeyboardButton


__all__ = ('pass_btn', 'get_feedback_btn')


pass_btn = [
    KeyboardButton('Пропустить', callback_data='pass')
]


def get_feedback_btn(task_id):
    smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
    btn = [KeyboardButton(smile, callback_data=f'feedback-{i + 1}-{task_id}') for i, smile in enumerate(smiles)]
    return btn
