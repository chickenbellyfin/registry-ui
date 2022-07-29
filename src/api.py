import base64
from typing import List

import aiohttp


class UnauthorizedApiError(Exception):
  pass

class ApiCredentials:
  def __init__(self, username, password):
    self.headers = {}
    if username and password:
      creds = base64.b64encode(bytes(f'{username}:{password}', 'utf-8')).decode('ascii')
      self.headers = {'Authorization': f'Basic {creds}'}

class DockerApiV2():

  def __init__(self, base_url: str, username: str = None, password: str = None):
    if base_url.endswith('/'):
      self.base_url = base_url[:-1]
    else:
      self.base_url = base_url

    self.headers = {
      'Accept': 'application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json'
    }
    self.headers.update(ApiCredentials(username, password).headers)
    self.session = None
    self.count = 0

  async def _get(self, path, headers=None, creds=None):
    if self.session is None:
      self.session = aiohttp.ClientSession()

    req_headers = {**self.headers}
    if headers:
      req_headers.update(headers)
    if creds:
      req_headers.update(creds.headers)
    async with self.session.get(self.base_url + path, headers=req_headers) as res:
      if res.status == 401:
        raise UnauthorizedApiError
      self.count += 1
      return await res.json(content_type=None)

  async def get_catalog(self, creds=None) -> List[str]:
    res = await self._get('/v2/_catalog', creds=creds)
    return res['repositories']

  async def get_tags(self, repo, creds=None) -> List[str]:
    res = await self._get(f'/v2/{repo}/tags/list', creds=creds)
    return res['tags']

  async def get_manifest(self, repo, tag, creds=None) -> dict:
    return await self._get(f'/v2/{repo}/manifests/{tag}', creds=creds)

  async def get_manifest_list(self, repo, tag, creds=None) -> List[dict]:
    res = await self._get(
      f'/v2/{repo}/manifests/{tag}',
      headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.manifest.v1+json'},
      creds=creds
    )
    if res.get('manifests') is None:
      return [res]
    else:
      return res['manifests']

  async def get_blob(self, repo, digest, creds=None) -> dict:
    return await self._get(f'/v2/{repo}/blobs/{digest}', creds=creds)
