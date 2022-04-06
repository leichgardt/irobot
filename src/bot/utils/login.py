from src.parameters import HOST_URL


def get_login_url(hash_code: str):
    return f'{HOST_URL}/login?hash_code={hash_code}'
