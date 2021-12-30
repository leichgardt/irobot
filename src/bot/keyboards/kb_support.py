def get_support_kb(client_chat_id):
    return (
        (
            {'text': 'Принять запрос', 'callback_data': f'get-support-line-{client_chat_id}'},
        ),
    )
