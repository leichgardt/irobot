from typing import Optional

from pydantic import UUID4, BaseModel, Field, validator


class OperCreate(BaseModel):
    login: str
    full_name: str
    password: str


class OperBase(BaseModel):
    oper_id: int
    login: str
    full_name: str
    enabled: bool
    root: bool


class TokenBase(BaseModel):
    token: UUID4 = Field(..., alias='access_token')
    expires: int
    token_type: Optional[str] = 'bearer'

    class Config:
        allow_population_by_field_name = True

    @classmethod
    @validator('token')
    def hexlify_token(cls, value):
        """ Конвертирует UUID в hex строку """
        return value.hex


class Oper(OperBase):
    """ Формирует тело ответа с деталями пользователя и токеном """
    token: TokenBase = {}
