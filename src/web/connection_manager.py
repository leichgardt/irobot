from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, oper_id: int):
        await websocket.accept()
        if oper_id in self.connections:
            self.connections[oper_id].append(websocket)
        else:
            self.connections[oper_id] = [websocket]

    def remove(self, websocket: WebSocket):
        for oper_id in self.connections:
            if websocket in self.connections[oper_id]:
                self.connections[oper_id].remove(websocket)

    async def _send_json(self, connection, data: dict):
        try:
            await connection.send_json(data)
        except WebSocketDisconnect:
            self.remove(connection)

    async def broadcast(self, action: str, data: dict):
        for connections in self.connections.values():
            for connection in connections:
                await self._send_json(connection, {'action': action, 'data': data})

    async def send_to_oper(self, oper_id: int, data: dict):
        for connection, oper in self.connections:
            if oper.oper_id == oper_id:
                await self._send_json(connection, data)
