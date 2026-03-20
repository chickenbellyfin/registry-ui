from unittest.mock import AsyncMock

import pytest
from sanic import Sanic

from src.api import DockerApiV2
from src.app import create_app

Sanic.test_mode = True


@pytest.fixture
def mock_api() -> DockerApiV2:
  return AsyncMock()

@pytest.fixture
def test_app(mock_api) -> Sanic:
    app = create_app(
      url='http://test',
      registry=mock_api,
      theme='auto',
      enable_login=False,
      display_name='test display name'
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
async def test_get_repo_oci_index(test_app: Sanic, mock_api: DockerApiV2):
  """Test tag listing when registry returns an OCI image index (multi-platform manifest)"""
  mock_api.get_tags.return_value = ['tag1']
  single_manifest = {
    'config': {
      'digest': 'sha256:12345678',
      'Env': {},
      'size': 1
    },
    'layers': [],
  }
  oci_index = {
    'schemaVersion': 2,
    'mediaType': 'application/vnd.oci.image.index.v1+json',
    'manifests': [
      {
        'mediaType': 'application/vnd.oci.image.manifest.v1+json',
        'digest': 'sha256:amd64digest',
        'size': 2583,
        'platform': {'architecture': 'amd64', 'os': 'linux'}
      },
      {
        'mediaType': 'application/vnd.oci.image.manifest.v1+json',
        'digest': 'sha256:attestdigest',
        'size': 566,
        'annotations': {
          'vnd.docker.reference.digest': 'sha256:amd64digest',
          'vnd.docker.reference.type': 'attestation-manifest'
        },
        'platform': {'architecture': 'unknown', 'os': 'unknown'}
      }
    ]
  }
  # First call returns OCI index, second call (by digest) returns the real manifest
  mock_api.get_manifest.side_effect = [oci_index, single_manifest]
  mock_api.get_blob.return_value = {
    'config': {'Env': {}},
    'architecture': 'amd64',
    'os': 'linux',
    'created': '2022-01-01T00:00:00.00Z',
    'history': []
  }
  request, response = await test_app.asgi_client.get("/repo?repo=test_repo")
  assert response.status == 200
  assert 'tag1' in response.text
  # Verify it resolved the index by fetching the platform manifest digest
  mock_api.get_manifest.assert_any_call('test_repo', 'sha256:amd64digest', creds=None)

@pytest.mark.asyncio
async def test_get_image(test_app: Sanic, mock_api: DockerApiV2):
  mock_api.get_manifest_list.return_value = [{
    'config': {
      'digest': 'sha256:12345678',
      'Env': {},
      'size': 1
    },
    'layers': [
      { 'size': 1, 'digest': 'sha256:abcdef012345'}
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
    'history': [
      { 'created': '2022-01-01T01:00:00.00Z', 'created_by': 'test_command2', 'empty_layer': True},
      { 'created': '2022-01-01T00:00:00.00Z', 'created_by': 'test_command'}
    ]
  }
  request, response = await test_app.asgi_client.get("/image?repo=test_repo&tag=test_tag")
  assert response.status == 200
  # image metadata
  assert 'test_repo:test_tag' in response.text
  assert 'test_os/test_arch' in response.text
  assert '2 B' in response.text # total size
  assert '/test/entrypoint --flag' in response.text
  assert 'Jan 01 2022 00:00:00 AM' in response.text

  # layers
  assert 'abcdef0' in response.text # formatted sha256

@pytest.mark.asyncio
async def test_get_image_oci_index(test_app: Sanic, mock_api: DockerApiV2):
  """Test image detail when registry returns manifest list with attestation manifests"""
  mock_api.get_manifest_list.return_value = [
    {
      'mediaType': 'application/vnd.oci.image.manifest.v1+json',
      'digest': 'sha256:amd64digest',
      'size': 2583,
      'platform': {'architecture': 'amd64', 'os': 'linux'}
    },
    {
      'mediaType': 'application/vnd.oci.image.manifest.v1+json',
      'digest': 'sha256:attestdigest',
      'size': 566,
      'annotations': {
        'vnd.docker.reference.digest': 'sha256:amd64digest',
        'vnd.docker.reference.type': 'attestation-manifest'
      },
      'platform': {'architecture': 'unknown', 'os': 'unknown'}
    }
  ]
  mock_api.get_manifest.return_value = {
    'config': {
      'digest': 'sha256:12345678',
      'Env': {},
      'size': 1
    },
    'layers': [
      { 'size': 1, 'digest': 'sha256:abcdef012345'}
    ],
  }
  mock_api.get_blob.return_value = {
    'config': {
      'Entrypoint': ['/test/entrypoint'],
      'Env': {},
    },
    'architecture': 'amd64',
    'os': 'linux',
    'created': '2022-01-02T00:00:00.00Z',
    'history': [
      { 'created': '2022-01-01T00:00:00.00Z', 'created_by': 'test_command'}
    ]
  }
  request, response = await test_app.asgi_client.get("/image?repo=test_repo&tag=test_tag")
  assert response.status == 200
  assert 'linux/amd64' in response.text
  # Attestation manifest should have been filtered — only one image fetched
  mock_api.get_manifest.assert_called_once_with('test_repo', 'sha256:amd64digest', creds=None)
