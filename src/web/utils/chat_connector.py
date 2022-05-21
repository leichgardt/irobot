import asyncio

import ujson
from aiologger import Logger
from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedOK

from src.modules.cache_storage.schemas.server_full import CacheServer
from src.web.schemas.ops import Oper
from src.web.utils import chat_actions
from src.web.utils.connection_manager import ConnectionManager


class ChatConnector:

    def __init__(
            self,
            manager: ConnectionManager,
            websocket: WebSocket,
            oper: Oper,
            logger: Logger,
            cache_storage: CacheServer
    ):
        self.manager = manager
        self.websocket = websocket
        self.oper = oper
        self.logger = logger
        self.pubsub = cache_storage.api.get_pubsub()

    async def handle_connection(self):
        target_task = self._get_target_connection_handler()
        broadcast_task = self._get_broadcast_handler()
        done, pending = await asyncio.wait(
            [target_task, broadcast_task],
            return_when=asyncio.FIRST_COMPLETED,
            loop=asyncio.get_running_loop(),
        )
        for task in pending:
            task.cancel()
            await self.manager.remove(self.websocket, self.oper.oper_id)

    async def _get_target_connection_handler(self):
        try:
            while True:
                input_data = await self.websocket.receive_json()
                action = input_data.get('action')
                data = input_data.get('data')
                func = chat_actions.actions.get_func(action)
                if func:
                    await func(self.websocket, self.manager, self.oper, data)
                else:
                    await self.logger.warning(f'Received unknown action "{action}" from {self.oper.login}')
                    await self.websocket.send_json({'action': 'answer', 'data': 'data received'})
        except (WebSocketDisconnect, ConnectionClosedOK):
            await self.manager.remove(self.websocket, self.oper.oper_id)
        except Exception as e:
            await self.manager.remove(self.websocket, self.oper.oper_id)
            await self.logger.exception(f'WebSocket error for oper={self.oper.oper_id}: {e}')

    async def _get_broadcast_handler(self):
        await self.pubsub.subscribe('chat')
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await self.websocket.send_json(ujson.loads(message.get('data')))
        except (WebSocketDisconnect, ConnectionClosedOK):
            await self.manager.remove(self.websocket, self.oper.oper_id)
            await self.pubsub.unsubscribe()
        except Exception as e:
            await self.manager.remove(self.websocket, self.oper.oper_id)
            await self.pubsub.unsubscribe()
            if 'a close message has been sent' not in str(e):
                await self.logger.exception(f'WebSocket error for oper={self.oper.oper_id}: {e}')
