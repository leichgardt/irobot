from src.web.utils import opers as opers_utils
from fastapi import Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/api/auth")


async def get_current_oper(token: str = Depends(oauth2_scheme)):
    print('token', token)
    if not token:
        return RedirectResponse('admin/auth')
    oper = await opers_utils.get_oper_by_token(token)
    if not oper:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    if not oper['enabled']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Inactive user')
    return oper
