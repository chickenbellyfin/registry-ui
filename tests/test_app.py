from unittest.mock import AsyncMock, MagicMock
import pytest
from sanic import Sanic
from src.api import DockerApiV2
from src.app import create_app

@pytest.fixture
def mock_api() -> DockerApiV2:
  return AsyncMock()

@pytest.fixture
def test_app(mock_api) -> Sanic:
    app = create_app(
      url='http://test',
      registry=mock_api,
      theme='auto',
      enable_login=False
    )
    return app

@pytest.mark.asyncio
async def test_get_catalog(test_app: Sanic, mock_api: DockerApiV2):
  mock_api.get_catalog.return_value = ['test_repo1', 'test_repo2']
  request, response = await test_app.asgi_client.get("/")
  assert response.status == 200
  assert 'test_repo1' in response.text
  assert 'test_repo2' in response.text

@pytest.mark.asyncio
async def test_get_repo(test_app: Sanic, mock_api: DockerApiV2):
  mock_api.get_tags.return_value = ['tag1', 'tag2', 'tag3']
  mock_api.get_manifest.return_value = {
    'config': {
      'digest': 'sha256:12345678',
      'Env': {},
      'size': 1
    },
    'layers': [],
  }
  request, response = await test_app.asgi_client.get("/repo?repo=test_repo")
  assert response.status == 200
  assert 'test_repo' in response.text
  assert 'tag1' in response.text
  assert 'tag2' in response.text
  assert 'tag3' in response.text

@pytest.mark.asyncio
async def test_get_image(test_app: Sanic, mock_api: DockerApiV2):
  mock_api.get_manifest_list.return_value = [{
    'config': {
      'digest': 'sha256:12345678',
      'Env': {},
      'size': 1
    },
    'layers': [
      { 'size': 1 }
    ],
  }]
  mock_api.get_blob.return_value = {
    'config': {
      'Entrypoint': ['/test/entrypoint', '--flag'],
      'Env': {},
    },
    'architecture': 'test_arch',
    'os': 'test_os',
    'created': '2022-01-02T00:00:00.00Z',
    'history': [{ 'created': '2022-01-01T00:00:00.00Z', 'created_by': 'test_command'}]
  }
  request, response = await test_app.asgi_client.get("/image?repo=test_repo&tag=test_tag")
  print(response.text)
  assert response.status == 200
  assert 'test_repo:test_tag' in response.text
  assert 'test_os/test_arch' in response.text
  assert '2 B' in response.text # total size
  assert '/test/entrypoint --flag' in response.text
  assert 'Jan 01 2022 00:00:00 AM' in response.text
