from typing import Dict, List, Union

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

    async def broadcast(
            self,
            action: str,
            data,
            firstly: WebSocket = None,
            ignore_list: List[Union[WebSocket, int]] = None
    ):
        if firstly:
            await firstly.send_json({'action': action, 'data': data})
        for oper_id, connections in self.connections.items():
            for connection in connections:
                if connection is firstly:
                    continue
                if ignore_list and (oper_id in ignore_list or connection in ignore_list):
                    continue
                await connection.send_json({'action': action, 'data': data})

    async def send_to_oper(self, oper_id: int, data: dict):
        for connection_oper_id, connections in self.connections.items():
            if connection_oper_id == oper_id:
                for connection in connections:
                    await connection.send_json(data)
