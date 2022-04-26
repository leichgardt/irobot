from typing import Dict, Type

from fastapi import WebSocket

from src.web.schemas.ops import Oper
from src.web.utils import chat as chat_utils
from src.web.utils.connection_manager import ConnectionManager

__all__ = 'actions',


class Action:

    def __init__(self, title: str):
        self.title = title

    def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        raise NotImplementedError()


class Actions:
    actions: Dict[str, Action] = {}

    def add_action(self, action_class: Type[Action], *titles: str):
        for title in titles:
            self.actions[title] = action_class(title)

    def get_func(self, title: str) -> Action.func:
        if title not in self.actions:
            return
        return self.actions[title].func


class GetChats(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        chats = await chat_utils.get_accounts_and_chats()
        await websocket.send_json({'action': 'get_chats', 'data': chats})


class GetChat(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        output = await chat_utils.get_chat_messages(data['chat_id'], data['message_id'])
        await websocket.send_json({'action': self.title, 'data': output})


class SendMessage(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        msg = await chat_utils.send_oper_message(data, oper.oper_id, oper.full_name)
        await manager.broadcast('get_message', msg, firstly=websocket)


class TakeChat(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        await chat_utils.take_chat(data, oper.oper_id)
        output = {'chat_id': data, 'oper_id': oper.oper_id, 'oper_name': oper.full_name}
        await manager.broadcast('take_chat', output, firstly=websocket)


class DropChat(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        await chat_utils.drop_chat(data, oper.oper_id)
        await manager.broadcast('drop_chat', {'chat_id': data}, firstly=websocket)


class FinishSupport(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        await chat_utils.finish_support(data, oper.oper_id, oper.full_name)
        chats = await chat_utils.get_accounts_and_chats()
        output = {'chat_id': data, 'oper_id': oper.oper_id, 'chats': chats}
        await manager.broadcast('finish_support', output, firstly=websocket)
        # todo show results: messages count, time left, operators in the support


class ReadChat(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        await chat_utils.read_chat(data)
        chats = await chat_utils.get_accounts_and_chats()
        await manager.broadcast('get_chats', chats, firstly=websocket)


class CheckMessages(Action):
    async def func(self, websocket: WebSocket, manager: ConnectionManager, oper: Oper, data):
        messages = [int(i) for i in data['list']]
        missed_message_ids = [i for i in range(min(messages), max(messages) + 1) if i not in messages]
        if missed_message_ids:
            chats = await chat_utils.get_chat_messages(data['chat_id'], id_list=missed_message_ids)
            for message in chats['messages'].values():
                message['chat_id'] = data['chat_id']
                await websocket.send_json({'action': 'get_message', 'data': message})


actions = Actions()
actions.add_action(GetChats, 'get_chats')
actions.add_action(GetChat, 'get_chat', 'load_messages')
actions.add_action(SendMessage, 'send_message')
actions.add_action(TakeChat, 'take_chat')
actions.add_action(DropChat, 'drop_chat')
actions.add_action(FinishSupport, 'finish_support')
actions.add_action(ReadChat, 'read_chat')
actions.add_action(CheckMessages, 'check_messages')
