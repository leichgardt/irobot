pass_btn = (
    (
        {'text': 'Пропустить', 'callback_data': 'pass'},
    ),
)


def get_feedback_btn(task_id):
    smiles = [':one:', ':two:', ':three:', ':four:', ':five:']
    btn = ([{'text': smile, 'callback_data': f'feedback-{i + 1}-{task_id}'} for i, smile in enumerate(smiles)],)
    return btn
