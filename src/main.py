import argparse
import os

from loguru import logger
from sanic import Sanic
from sanic.worker.loader import AppLoader

from src import app
from src.api import DockerApiV2


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
  enable_login =  args.enable_login or env_bool('APP_ENABLE_LOGIN', True)
  username = args.username or os.environ.get('REGISTRY_USERNAME')
  password = args.password or os.environ.get('REGISTRY_PASSWORD')

  theme = os.environ.get('APP_THEME', 'auto')
  if theme not in app.THEME_CSS:
    logger.warning(f'Theme "{theme}" is not valid. Must be one of {",".join(app.THEME_CSS.keys())}')
    theme = 'auto'
  logger.info(f'UI Theme is "{theme}"')

  registry = DockerApiV2(
    URL,
    username=username,
    password=password
  )
  return app.create_app(URL, registry, theme, enable_login=enable_login)


if __name__ == '__main__':
    loader = AppLoader(factory=main)
    app = loader.load()
    app.prepare(host='0.0.0.0', dev=env_bool('APP_DEBUG', True))
    Sanic.serve(primary=app, app_loader=loader)
