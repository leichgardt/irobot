from typing import List, Tuple

from fastapi import WebSocket

import src.web.schemas.opers as opers


class ConnectionManager:
    def __init__(self):
        self.connections: List[Tuple[WebSocket, opers.Oper]] = []

    async def connect(self, websocket: WebSocket, operator: opers.Oper):
        await websocket.accept()
        self.connections.append((websocket, operator))

    def remove(self, websocket: WebSocket):
        for i in range(len(self.connections)):
            if websocket in self.connections[i]:
                self.connections.pop(i)

    async def broadcast(self, action: str, data: dict):
        for connection, oper in self.connections:
            await connection.send_json({'action': action, 'data': data})
