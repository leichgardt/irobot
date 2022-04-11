from pydantic import BaseModel


class LoginItem(BaseModel):
    login: str
    pwd: str
    hash: str
