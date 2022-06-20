

"""
Methods for higher level data fetching from docker registry API. These should map to UI
components and may make multiple API calls and app-specific data transformations.
"""
import asyncio
from datetime import datetime
from dateutil import parser
import re

from src import util
from src.api import DockerApiV2

def format_command(created_by: str) -> str:
  return re.sub('/bin/sh -c (#\(nop\) )?', '', created_by)

def format_digest(sha256: str) -> str:
  """ sha256 is "sha256:$hash" """
  return sha256.split(':')[1][:7]

def format_date(date: datetime) -> str:
  return date.strftime('%b %d %Y %H:%M:%S %p')

def format_layer(layer):
  # todo - this is not correct
  # manifest only lists non-empty layers
  result = {**layer}
  result['date'] = format_date(parser.parse(layer['created']))
  result['command'] = format_command(layer['created_by'])
  if layer.get('size'):
    result['size_h'] = util.bytes_str(layer['size'])
  if result.get('digest'):
    result['short_digest'] =  format_digest(layer['digest'])

  return result

def merge_layers(layers, history):
  result = []
  layer_idx = 0
  for h in history:
    if not h.get('empty_layer'):
      result.append({**layers[layer_idx], **h})
      layer_idx += 1
    else:
      result.append(h)
  result.reverse() # reverse so that newer layers are first
  return list(map(format_layer, result))


async def fetch_repositories(api: DockerApiV2, creds=None):
  repositories = await api.get_catalog(creds=creds)
  tags = await asyncio.gather(*[api.get_tags(r, creds=creds) for r in repositories])
  return [
    {
      'repo': repo,
      'tag_count': len(tag_list)
    }
    for repo, tag_list in zip(repositories, tags)
  ]


async def fetch_tags(api: DockerApiV2, repo, creds=None):
  tags = await api.get_tags(repo, creds=creds)

  # fetch more details for each tag
  images = await asyncio.gather(*[fetch_image(api, repo, t, creds=creds) for t in tags])
  details = []
  for tag, image in zip(tags, images):
    details.append({
      'tag': tag,
      'size': image['size'],
      'sizeh': util.bytes_str(image['size']),
      'date': image['date']
    })
  return details


async def fetch_image(api: DockerApiV2, repo, tag, creds=None):
  manifest = await api.get_manifest(repo, tag, creds=creds)
  digest = manifest['config']['digest']
  blob = await api.get_blob(repo, digest, creds=creds)

  total_size = manifest['config']['size']
  for layer in manifest['layers']:
    total_size += layer['size']

  layers = merge_layers(manifest['layers'], blob['history'])

  if blob['config'].get('Entrypoint'):
    entrypoint = ' '.join(blob['config']['Entrypoint'])
  else:
    entrypoint = None

  if blob['config'].get('Cmd'):
    cmd = ' '.join(blob['config']['Cmd'])
  else:
    cmd = None

  if blob['config'].get('ExposedPorts'):
    ports = ', '.join(blob['config']['ExposedPorts'].keys())
  else:
    ports = 'none'

  environment = []
  for s in blob['config']['Env']:
    environment.append({
      'key': s.split('=')[0],
      'value': s.split('=')[1]
    })

  return {
    'architecture': blob['architecture'],
    'os': blob['os'],
    'date': format_date(parser.parse(blob['created'])),
    'config': manifest['config'],
    'layers': layers,
    'size': total_size,
    'size_h': util.bytes_str(total_size),
    'entrypoint': entrypoint,
    'cmd': cmd,
    'ports': ports,
    'blob': blob,
    'environment': environment
  }
