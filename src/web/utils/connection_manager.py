import asyncio
from typing import Dict, List, Union

from starlette.websockets import WebSocket, WebSocketState


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}

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
            await self._send(firstly, {'action': action, 'data': data})
        async for oper_id, connections in self.get_all_connections():
            async for connection in self.get_next_connection(connections):
                if connection is firstly:
                    continue
                if ignore_list and (oper_id in ignore_list or connection in ignore_list):
                    continue
                await self._send(connection, {'action': action, 'data': data})

    async def _send(self, connection: WebSocket, data):
        if connection.application_state == WebSocketState.DISCONNECTED:
            self.remove(connection)
            return
        elif connection.application_state != WebSocketState.CONNECTED:
            await asyncio.sleep(5)
        try:
            await asyncio.wait_for(connection.send_json(data), timeout=5, loop=asyncio.get_running_loop())
        except:
            self.remove(connection)

    async def get_all_connections(self):
        for oper_id, connections in self.connections.items():
            yield oper_id, connections

    @staticmethod
    async def get_next_connection(connections):
        for connection in connections:
            yield connection
