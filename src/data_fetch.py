

"""
Methods for higher level data fetching from docker registry API. These should map to UI
components and may make multiple API calls and app-specific data transformations.
"""
from concurrent.futures import ThreadPoolExecutor

from dateutil import parser

from src import util
from src.api import DockerApiV2


def fetch_repositories(api: DockerApiV2):
  repositories = api.get_catalog()
  executor = ThreadPoolExecutor(max_workers=100)
  tags = executor.map(lambda r: api.get_tags(r), repositories)

  return [
    {
      'repo': repo,
      'tag_count': len(tags)
    }
    for repo, tags in zip(repositories, tags)
  ]


def fetch_tags(api: DockerApiV2, repo):
  tags = api.get_tags(repo)

  # fetch more details for each tag
  details = []
  executor = ThreadPoolExecutor(max_workers=100)
  images = executor.map(lambda t: fetch_image(api, repo, t), tags)
  for tag, image in zip(tags, images):
    details.append({
      'tag': tag,
      'size': image['size'],
      'sizeh': util.bytes_str(image['size']),
      'created': image['created']
    })
  return details


def fetch_image(api: DockerApiV2, repo, tag):
  manifest = api.get_manifest(repo, tag)
  digest = manifest['config']['digest']
  blob = api.get_blob(repo, digest)

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
