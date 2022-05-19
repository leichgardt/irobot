from aiologger import Logger

from config import CARDINALIS_URL
from src.utils import post_request


async def send_feedback_to_cardinalis(logger: Logger, input_task_id: int, input_text: str):
    if CARDINALIS_URL:
        res = await post_request(f'{CARDINALIS_URL}/api/save_feedback', logger=logger,
                                 json={'task_id': input_task_id, 'text': input_text, 'service': 'telegram'})
        return res.get('response', 0)
    return 0
