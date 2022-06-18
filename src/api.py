import base64

import requests


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

  def _get(self, path):
    res = requests.get(self.base_url + path, headers=self.headers)
    return res.json()

  def get_catalog(self):
    return self._get('/v2/_catalog')['repositories']

  def get_tags(self, repo):
    return self._get(f'/v2/{repo}/tags/list')['tags']

  def get_manifest(self, repo, tag):
    return self._get(f'/v2/{repo}/manifests/{tag}')

  def get_blob(self, repo, digest):
    return self._get(f'/v2/{repo}/blobs/{digest}')
