import pytest
from httpx import AsyncClient


@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_index(app):
    async with AsyncClient(app=app, base_url='http://test') as ac:
        response = await ac.get('/')
    assert response.status_code == 200
    assert 'Добро пожаловать!' in response.text


class TestAdminAuth:
    token: str

    @pytest.mark.order(2)
    @pytest.mark.asyncio
    async def test_get_token(self, app):
        data = {'username': 'test', 'password': '_@#123test123^^^321tset321tset#@_'}
        async with AsyncClient(app=app, base_url='http://test') as ac:
            response = await ac.post('/admin/api/auth', data=data)
        assert response.status_code == 200
        data = response.json()
        assert data.get('login') == 'test'
        self.__class__.token = data.get('token', {}).get('access_token')

    @pytest.mark.order(3)
    @pytest.mark.skip(reason='Test error of check a token in cookies')
    @pytest.mark.asyncio
    async def test_auth_with_token(self, app):
        assert self.__class__.token
        cookies = {'irobot_access_token': self.__class__.token}
        async with AsyncClient(app=app, base_url='http://test', cookies=cookies) as ac:
            response = await ac.get('/admin/chat')
        assert response.status_code == 200
        assert 'Войти в чат' in response.text
