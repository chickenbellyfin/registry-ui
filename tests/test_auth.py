from unittest.mock import AsyncMock

import pytest
from sanic_testing.testing import SanicASGITestClient

from src.api import DockerApiV2, UnauthorizedApiError
from src.app import create_app


@pytest.fixture
def mock_api() -> DockerApiV2:
  return AsyncMock()

@pytest.fixture
def test_client(mock_api) -> SanicASGITestClient:
    app = create_app(
      url='http://test',
      registry=mock_api,
      theme='auto',
      enable_login=True
    )
    return app.asgi_client

@pytest.mark.asyncio
async def test_auth_catalog_redir(test_client: SanicASGITestClient, mock_api: DockerApiV2):
  mock_api.get_catalog.side_effect = UnauthorizedApiError()
  request, response = await test_client.get("/")
  assert response.status == 302
  assert response.headers['Location'] == '/login'

@pytest.mark.asyncio
async def test_auth_tags_redir(test_client: SanicASGITestClient, mock_api: DockerApiV2):
  mock_api.get_tags.side_effect = UnauthorizedApiError()
  request, response = await test_client.get("/repo?repo=test_repo")
  assert response.status == 302
  assert response.headers['Location'] == '/login'

@pytest.mark.asyncio
async def test_auth_catalog_redir(test_client: SanicASGITestClient, mock_api: DockerApiV2):
  mock_api.get_manifest_list.side_effect = UnauthorizedApiError()
  request, response = await test_client.get("/image?repo=test_repo&tag=test_tag")
  assert response.status == 302
  assert response.headers['Location'] == '/login'

@pytest.mark.asyncio
async def test_login_flow(test_client: SanicASGITestClient, mock_api: DockerApiV2):
  mock_api.get_catalog.side_effect = UnauthorizedApiError()
  request, response = await test_client.get("/")
  assert response.status == 302 and response.headers['Location'] == '/login'

  request, response = await test_client.get("/login")
  assert response.status == 200
  assert 'action="/submit_login"' in response.text

  request, response = await test_client.post(
    '/submit_login',
    data={'username': 'testuser', 'password': 'testpass'}
  )

  assert response.status == 302
  assert response.headers['Location'] == '/'
  assert response.cookies['registry_username'] == 'testuser'
  assert response.cookies['registry_password'] == 'testpass'
