import argparse
import os
import re

from loguru import logger
from sanic import Sanic, response
from sanic_ext import render

from src.api import ApiCredentials, DockerApiV2, UnauthorizedApiError
from src.data_fetch import fetch_image_list, fetch_repositories, fetch_tags

THEME_CSS = {
  'light': 'light.min.css',
  'dark': 'dark.min.css',
  'auto': 'water.min.css'
}

def create_app(url: str, registry: DockerApiV2, theme: str, enable_login) -> Sanic:
  app = Sanic(__name__)

  # extra context for jinja templates
  context = {
    'site': re.sub('https?://', '', url),
    'theme': THEME_CSS[theme]
  }

  app.static('/static', 'static')

  def auth(func):
    if not enable_login:
      return func

    async def wrapped(request, *args, **kwargs):
      try:
        username = request.cookies.get('registry_username')
        password = request.cookies.get('registry_password')
        creds = ApiCredentials(username, password)
        return await func(request, *args, **kwargs, creds=creds)
      except UnauthorizedApiError as e:
        res = response.redirect('/login')
        del res.cookies['registry_username']
        del res.cookies['registry_password']
      return res
    return wrapped

  @app.get('/login')
  async def login(request):
    response = await render('login.html', context={'context': context})
    return response

  @app.post('/submit_login')
  async def submit_login(request):
    res = response.redirect('/')
    res.cookies['registry_username'] = request.form.get('username')
    res.cookies['registry_password'] = request.form.get('password')
    return res

  @app.get('/')
  @auth
  async def list_repositories(request, creds=None):
    repositories = await fetch_repositories(registry, creds=creds)
    return await render(
      'repositories.html', context={
        'context': context,
        'repositories': repositories
      })

  @app.get('/repo')
  @auth
  async def list_tags(request, creds=None):
    repo = request.args.get('repo')
    tags = await fetch_tags(registry, repo, creds=creds)
    return await render('tags.html', context={
      'context': context,
      'tags': tags,
      'repo': repo
    })

  @app.get('/image')
  @auth
  async def tag_history(request, creds=None):
    repo = request.args.get('repo')
    tag = request.args.get('tag')
    images =  await fetch_image_list(registry, repo, tag, creds=creds) # registry.history(repo, tag)
    return await render('history.html', context={
      'context': context,
      'images': images,
      'repo': repo,
      'tag': tag
    })

  return app


def env_bool(name, default: bool):
  return os.environ.get(name, str(default)).lower() == 'true'

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-r', '--registry', dest='registry', help='Registry URL (with http:// or https://)')
  parser.add_argument('-l', '--login', dest='enable_login', action='store_true', help='Show a login page for registries which require basic auth.')
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

  # If username and password are set, the api will try to use those even if the user has not logged in.
  enable_login =  args.enable_login or env_bool('APP_ENABLE_LOGIN', False)
  username = args.username or os.environ.get('REGISTRY_USERNAME')
  password = args.password or os.environ.get('REGISTRY_PASSWORD')

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
  return create_app(URL, registry, theme, enable_login=enable_login)

app = main()

if __name__ == '__main__':
  app.run('0.0.0.0', debug=env_bool('APP_DEBUG', True))
