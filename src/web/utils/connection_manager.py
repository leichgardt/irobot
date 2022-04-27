import asyncio
from datetime import datetime
from threading import Thread
from typing import Dict, List, Union

from starlette.websockets import WebSocket, WebSocketState


class ConnectionManager:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.connections: Dict[int, List[WebSocket]] = {}
        self.threads: Dict[float, Thread] = {}

    async def connect(self, websocket: WebSocket, oper_id: int):
        await websocket.accept()
        if oper_id in self.connections:
            self.connections[oper_id].append(websocket)
        else:
            self.connections[oper_id] = [websocket]

    def remove(self, websocket: WebSocket, oper_id: int = None):
        if oper_id:
            if websocket in self.connections[oper_id]:
                self.connections[oper_id].remove(websocket)
        else:
            for connections in self.connections.values():
                if websocket in connections:
                    connections.remove(websocket)

    async def broadcast(
            self,
            action: str,
            data,
            firstly: WebSocket = None,
            ignore_list: List[Union[WebSocket, int]] = None
    ):
        if firstly:
            await self.send_into_thread(firstly, {'action': action, 'data': data})
        for oper_id, connections in self.connections.items():
            for connection in connections:
                if connection is firstly:
                    continue
                if ignore_list and (oper_id in ignore_list or connection in ignore_list):
                    continue
                await self.send_into_thread(connection, {'action': action, 'data': data})

    async def send_into_thread(self, connection: WebSocket, data):
        start = datetime.now().timestamp()
        self.threads[start] = Thread(target=self._send, args=(connection, data), daemon=True)
        self.threads[start].start()
        while datetime.now().timestamp() - start < 3 and self.threads[start].is_alive():
            await asyncio.sleep(0.1)
        if self.threads[start].is_alive():
            del self.threads[start]
        else:
            self.threads[start].join(1)

    def _send(self, connection: WebSocket, data: dict):
        if connection.application_state == WebSocketState.DISCONNECTED:
            self.remove(connection)
        elif connection.application_state == WebSocketState.CONNECTED:
            self.loop.create_task(self._try_send(connection, data))

    @staticmethod
    async def _try_send(connection: WebSocket, data):
        try:
            await connection.send_json(data)
        except:
            pass
