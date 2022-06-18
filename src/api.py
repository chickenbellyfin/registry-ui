import base64
import aiohttp
from loguru import logger

class DockerApiV2():

  def __init__(self, base_url: str, username: str = None, password: str = None):
    if base_url.endswith('/'):
      self.base_url = base_url[:-1]
    else:
      self.base_url = base_url

    self.headers = {
      'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
    }
    if username and password:
      creds = base64.b64encode(bytes(f'{username}:{password}', 'utf-8')).decode('ascii')
      self.headers['Authorization'] = f'Basic {creds}'
    self.session = None
    self.count = 0

  async def _get(self, path):
    if self.session is None:
      self.session = aiohttp.ClientSession(base_url=self.base_url)
    async with self.session.get(path, headers=self.headers) as res:
      self.count += 1
      return await res.json(content_type=None)

  async def get_catalog(self):
    res = await self._get('/v2/_catalog')
    return res['repositories']

  async def get_tags(self, repo):
    res = await self._get(f'/v2/{repo}/tags/list')
    return res['tags']

  async def get_manifest(self, repo, tag):
    return await self._get(f'/v2/{repo}/manifests/{tag}')

  async def get_blob(self, repo, digest):
    return await self._get(f'/v2/{repo}/blobs/{digest}')
