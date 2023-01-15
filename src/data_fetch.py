

"""
Methods for higher level data fetching from docker registry API. These should map to UI
components and may make multiple API calls and app-specific data transformations.
"""
import asyncio
import re
from datetime import datetime
from typing import Union

from dateutil import parser

from src import util
from src.api import DockerApiV2


def format_command(created_by: str) -> str:
  return re.sub('/bin/sh -c (#\(nop\) )?', '', created_by)

def format_digest(sha256: str) -> str:
  """ sha256 is "sha256:$hash" """
  return sha256.split(':')[1][:7]

def format_date(date: Union[str, datetime]) -> str:
  if type(date) == str:
    date = parser.parse(date)
  return date.strftime('%b %d %Y %H:%M:%S %p')

def format_layer(layer: dict):
  return {
    'date': format_date(layer['created']),
    'command': format_command(layer['created_by']),
    'size': util.format_bytes(layer['size']) if layer.get('size') else None,
    'digest_short': format_digest(layer['digest']) if layer.get('digest') else None
  }

def merge_layers(layers, history):
  """ Merges the layers from a manifest with the history of the blob referenced by the manifest's
  digest. Each non-empty item in the blob history is paired with the layers in order"""
  result = []
  layer_idx = 0
  for item in history:
    if not item.get('empty_layer'):
      result.append({**layers[layer_idx], **item})
      layer_idx += 1
    else:
      result.append(item)
  result.reverse() # reverse so that newer layers are first
  return list(map(format_layer, result))


async def fetch_repositories(api: DockerApiV2, creds=None):
  repositories = await api.get_catalog(creds=creds)
  tags = await asyncio.gather(*[api.get_tags(r, creds=creds) for r in repositories])
  return [
    {
      'repo': repo,
      'tag_count': 0 if tag_list is None else len(tag_list)
    }
    for repo, tag_list in zip(repositories, tags)
  ]


async def fetch_tags(api: DockerApiV2, repo, creds=None):
  tags = await api.get_tags(repo, creds=creds)
  if tags is None:
    return []

  # fetch more details for each tag
  images = await asyncio.gather(*[fetch_image(api, repo, t, creds=creds) for t in tags])
  details = []
  for tag, image in zip(tags, images):
    details.append({
      'tag': tag,
      'size': image['size'],
      'date': image['date']
    })
  return details

async def fetch_manifest_details(api: DockerApiV2, repo, manifest=None, manifest_digest=None, creds=None):
  """ Fetch image details given a manifest or a digest
  If we get a digest, we must first fetch the manifest
  """
  if manifest is not None:
    digest = manifest['config']['digest']
  else:
    manifest = await api.get_manifest(repo, manifest_digest, creds=creds)
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
    'working_dir': blob['config'].get('WorkingDir', '(unset)'),
    'date': format_date(blob['created']),
    'layers': layers,
    'size': util.format_bytes(total_size),
    'entrypoint': entrypoint,
    'cmd': cmd,
    'ports': ports,
    'blob': blob,
    'environment': environment
  }


async def fetch_image(api: DockerApiV2, repo, tag, creds=None):
  manifest = await api.get_manifest(repo, tag, creds=creds)
  return await fetch_manifest_details(api, repo, manifest, creds=creds)

async def fetch_image_list(api: DockerApiV2, repo, tag, creds=None):
  manifests = await api.get_manifest_list(repo, tag, creds=creds)

  # docker API might return a manifest or a manifest list
  # if it returns a manifest, it has .config.digest, otherwise the manifest has .digest
  images = []
  for manifest in manifests:
    if manifest.get('config'):
      images.append(fetch_manifest_details(api, repo, manifest=manifest, creds=creds))
    else:
      images.append(fetch_manifest_details(api, repo, manifest_digest=manifest['digest'], creds=creds))

  return await asyncio.gather(*images)
