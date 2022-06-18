import os
import re
import sys

from quart import Quart, render_template
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

def create_app(url: str, registry: DockerApiV2, theme: str) -> Quart:
  app = Quart(__name__)

  # extra context for jinja templates
  context = {
    'site': re.sub('https?://', '', url),
    'theme': THEME_CSS[theme]
  }

  @app.route('/')
  async def list_repositories():
    repositories = await fetch_repositories(registry)
    return await render_template(
      'repositories.html', context=context, repositories=repositories)

  @app.route('/repo/<repo>')
  async def list_tags(repo: str):
    tags = await fetch_tags(registry, repo)
    return await render_template('tags.html', context=context, tags=tags, repo=repo)

  @app.route('/image/<repo>/<tag>')
  async def tag_history(repo, tag):
    # history = (config + layers) aka image
    history =  await fetch_image(registry, repo, tag) # registry.history(repo, tag)
    history['size_h'] = util.bytes_str(history['size'])
    for layer in history['layers']:
      layer['size_h'] = util.bytes_str(layer['size'])
    return await render_template('history.html',
      context=context,
      history=history,
      repo=repo,
      tag=tag
    )

  return app


def main():

  if len(sys.argv) > 1:
    URL = sys.argv[1]
  else:
    URL = os.environ.get('REGISTRY_URL')

  if not URL:
    logger.error(f'Registry URL is required')
    exit(1)

  if not URL.startswith('http://') and not URL.startswith('https://'):
    logger.error(f'URL "{URL}" must start with http:// or https://')
    exit(1)

  username = os.environ.get('REGISTRY_USERNAME')
  password = os.environ.get('REGISTRY_PASSWORD')

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
  app = create_app(URL, registry, theme)
  app.run(host="0.0.0.0")

if __name__ == '__main__':
  main()
