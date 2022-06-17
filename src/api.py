import base64
from concurrent.futures import ThreadPoolExecutor

import requests
from dateutil import parser

from src import util


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

  def get_tags(self, repo):
    return self._get(f'/v2/{repo}/tags/list')['tags']

  def repositories(self):
    res = self._get('/v2/_catalog')
    repos = res['repositories']
    executor = ThreadPoolExecutor(max_workers=100)
    tags = executor.map(lambda r: self.get_tags(r), repos)

    return [
      {
        'repo': repo,
        'tag_count': len(tags)
      }
      for repo, tags in zip(repos, tags)
    ]


  def get_image(self, repo, tag):
    manifest = self._get(f'/v2/{repo}/manifests/{tag}')
    digest = manifest['config']['digest']
    blob = self._get(f'/v2/{repo}/blobs/{digest}')

    total_size = manifest['config']['size']
    for layer in manifest['layers']:
      total_size += layer['size']

    layers = []
    for layer_item, history_item in zip(manifest['layers'], blob['history']):
      layers.append({**layer_item, **history_item})

    return {
      'architecture': blob['architecture'],
      'os': blob['os'],
      'created': parser.parse(blob['created']),
      'config': manifest['config'],
      'layers': layers,
      'size': total_size
    }


  def tags(self, repo):
    tags = self.get_tags(repo)

    # fetch more details for each tag
    details = []
    executor = ThreadPoolExecutor(max_workers=100)
    images = executor.map(lambda t: self.get_image(repo, t), tags)
    for tag, image in zip(tags, images):
      details.append({
        'tag': tag,
        'size': image['size'],
        'sizeh': util.bytes_str(image['size']),
        'created': image['created']
      })
    return details


  def history(self, repo, tag):
    return self.get_image(repo, tag)
