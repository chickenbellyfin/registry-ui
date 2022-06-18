

"""
Methods for higher level data fetching from docker registry API. These should map to UI
components and may make multiple API calls and app-specific data transformations.
"""
import asyncio
from dateutil import parser

from src import util
from src.api import DockerApiV2


async def fetch_repositories(api: DockerApiV2):
  repositories = await api.get_catalog()
  tags = await asyncio.gather(*[api.get_tags(r) for r in repositories])
  return [
    {
      'repo': repo,
      'tag_count': len(tag_list)
    }
    for repo, tag_list in zip(repositories, tags)
  ]


async def fetch_tags(api: DockerApiV2, repo):
  tags = await api.get_tags(repo)

  # fetch more details for each tag
  images = await asyncio.gather(*[fetch_image(api, repo, t) for t in tags])
  details = []
  for tag, image in zip(tags, images):
    details.append({
      'tag': tag,
      'size': image['size'],
      'sizeh': util.bytes_str(image['size']),
      'created': image['created']
    })
  return details


async def fetch_image(api: DockerApiV2, repo, tag):
  manifest = await api.get_manifest(repo, tag)
  digest = manifest['config']['digest']
  blob = await api.get_blob(repo, digest)

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
