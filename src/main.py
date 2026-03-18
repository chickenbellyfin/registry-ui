import os

from sanic import Sanic
from sanic.worker.loader import AppLoader

from src import app
from src.api import DockerApiV2
from src import config


def env_bool(name, default: bool):
  return os.environ.get(name, str(default)).lower() == 'true'

def main():
  registry = DockerApiV2(
    config.URL,
    username=config.USERNAME,
    password=config.PASSWORD
  )
  return app.create_app(config.URL, registry, config.THEME, enable_login=config.ENABLE_LOGIN, display_name=config.DISPLAY_NAME)


if __name__ == '__main__':
    loader = AppLoader(factory=main)
    app = loader.load()
    app.prepare(host='0.0.0.0', dev=config.APP_DEBUG)
    Sanic.serve(primary=app, app_loader=loader)
