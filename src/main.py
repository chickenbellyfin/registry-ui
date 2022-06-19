import argparse
import os
import re


from sanic import Sanic
from sanic_ext import render
from loguru import logger
from src.data_fetch import fetch_repositories

from src import util
from src.api import DockerApiV2
from src.data_fetch import fetch_tags, fetch_tags, fetch_image

THEME_CSS = {
  'light': 'light.min.css',
  'dark': 'dark.min.css',
  'auto': 'water.min.css'
}

def create_app(url: str, registry: DockerApiV2, theme: str) -> Sanic:
  app = Sanic(__name__)

  # extra context for jinja templates
  context = {
    'site': re.sub('https?://', '', url),
    'theme': THEME_CSS[theme]
  }

  app.static('/static', 'static')

  @app.route('/')
  async def list_repositories(request):
    repositories = await fetch_repositories(registry)
    return await render(
      'repositories.html', context={
        'context': context,
        'repositories': repositories
      })

  @app.route('/repo/<repo>')
  async def list_tags(request, repo: str):
    tags = await fetch_tags(registry, repo)
    return await render('tags.html', context={
      'context': context,
      'tags': tags,
      'repo': repo
    })

  @app.route('/image/<repo>/<tag>')
  async def tag_history(request, repo, tag):
    # history = (config + layers) aka image
    history =  await fetch_image(registry, repo, tag) # registry.history(repo, tag)
    history['size_h'] = util.bytes_str(history['size'])
    for layer in history['layers']:
      layer['size_h'] = util.bytes_str(layer['size'])
    return await render('history.html', context={
      'context': context,
      'history': history,
      'repo': repo,
      'tag': tag
    })

  return app


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-r', '--registry', dest='registry', help='Registry URL (with http:// or https://)')
  parser.add_argument('-u', '--username', dest='username', help='Username for registry basic auth')
  parser.add_argument('-p', '--password', dest='password', help='Password for registry basic auth')

  args, _ = parser.parse_known_args()

  if args.registry:
    URL = args.registry
  else:
    URL = os.environ.get('REGISTRY_URL')

  if not URL:
    logger.error(f'Registry URL is required')
    exit(1)

  if not URL.startswith('http://') and not URL.startswith('https://'):
    logger.error(f'URL "{URL}" must start with http:// or https://')
    exit(1)

  logger.info(f'Registry URL is {URL}')

  username = args.username or os.environ.get('REGISTRY_USERNAME')
  password = args.password or os.environ.get('REGISTRY_PASSWORD')
  print(username, password)

  theme = os.environ.get('APP_THEME', 'auto')
  if theme not in THEME_CSS:
    logger.warning(f'Theme "{theme}" is not valid. Must be one of {",".join(THEME_CSS.keys())}')
    theme = 'auto'
  logger.info(f'UI Theme is "{theme}"')

  registry = DockerApiV2(
    URL,
    username=username,
    password=password
  )
  return create_app(URL, registry, theme)

app = main()

if __name__ == '__main__':
  app.run('0.0.0.0', debug=os.environ.get('APP_DEBUG', 'true') != 'false')
