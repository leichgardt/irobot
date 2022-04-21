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
        for oper_id, connections in self.connections.items():
            for connection in connections:
                if connection.application_state == WebSocketState.DISCONNECTED:
                    self.remove(connection, oper_id)
                    continue
                if connection.application_state != WebSocketState.CONNECTED:
                    continue
                if connection is firstly:
                    continue
                if ignore_list and (oper_id in ignore_list or connection in ignore_list):
                    continue
                await connection.send_json({'action': action, 'data': data})

    async def _send(self, connection: WebSocket, data: dict):
        if connection.application_state == WebSocketState.DISCONNECTED:
            self.remove(connection)
        elif connection.application_state == WebSocketState.CONNECTED:
            await connection.send_json(data)
