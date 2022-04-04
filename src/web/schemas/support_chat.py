from typing import List

from pydantic import BaseModel


class MessageContent:
    type: str
    content: dict


class Message:
    message_id: int
    from_oper: int
    content: MessageContent


class Chat(BaseModel):
    chat_id: int
    messages: List[Message]

