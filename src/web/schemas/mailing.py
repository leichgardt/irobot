from pydantic import BaseModel


class Mail(BaseModel):
    type: str
    text: str
    parse_mode: str = None
