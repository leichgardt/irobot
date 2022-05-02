import asyncio
from typing import Dict, List, Union

from starlette.websockets import WebSocket, WebSocketState


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}
        self.timeout = 5

    async def connect(self, websocket: WebSocket, oper_id: int):
        await websocket.accept()
        if oper_id in self.connections:
            self.connections[oper_id].append(websocket)
        else:
            self.connections[oper_id] = [websocket]

    @staticmethod
    async def disconnect(websocket: WebSocket):
        try:
            await websocket.close()
        except:
            pass

    async def remove(self, websocket: WebSocket, oper_id: int = None):
        await self.disconnect(websocket)
        if oper_id and oper_id in self.connections:
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
        payload = {'action': action, 'data': data}
        if firstly:
            await self._send(firstly, payload)
        await asyncio.gather(
            *[self._send(connection, payload) for connection in self.get_connections(firstly, ignore_list)],
            loop=asyncio.get_running_loop()
        )

    async def _send(self, connection: WebSocket, data):
        if connection.application_state == WebSocketState.DISCONNECTED:
            await self.remove(connection)
            return
        elif connection.application_state != WebSocketState.CONNECTED:
            await asyncio.sleep(self.timeout)
        try:
            await asyncio.wait_for(connection.send_json(data), timeout=self.timeout, loop=asyncio.get_running_loop())
        except:
            await self.remove(connection)

    def get_connections(self, firstly: WebSocket = None, ignore_list: List[Union[WebSocket, int]] = None):
        for oper_id, connections in self.connections.items():
            for connection in connections:
                if connection is firstly:
                    continue
                if ignore_list and (oper_id in ignore_list or connection in ignore_list):
                    continue
                yield connection
