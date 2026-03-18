  
import argparse
import os

from loguru import logger

from src import app

def env_bool(name, default: bool):
  return os.environ.get(name, str(default)).lower() == 'true'

logger.info('Loading configuration...')

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--registry', dest='registry', help='Registry URL (with http:// or https://)')
parser.add_argument('-n', '--display-name', dest='display_name', help='Display name for the registry (optional, defaults to the registry URL)')
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

DISPLAY_NAME = args.display_name or os.environ.get('REGISTRY_DISPLAY_NAME') or URL
# If username and password are set, the api will try to use those even if the user has not logged in.
ENABLE_LOGIN =  args.enable_login or env_bool('APP_ENABLE_LOGIN', True)
USERNAME = args.username or os.environ.get('REGISTRY_USERNAME')
PASSWORD = args.password or os.environ.get('REGISTRY_PASSWORD')

THEME = os.environ.get('APP_THEME', 'auto')
if THEME not in app.THEME_CSS:
    logger.warning(f'Theme "{THEME}" is not valid. Must be one of {",".join(app.THEME_CSS.keys())}')
THEME = 'auto'

APP_DEBUG = env_bool('APP_DEBUG', False)

logger.info(f"""Loaded settings:
    Registry URL: {URL}
    Display Name: {DISPLAY_NAME}
    Enable Login: {ENABLE_LOGIN}
    Theme: {THEME}
    Debug: {APP_DEBUG}
    username: {"set" if USERNAME else "not set"}
    password: {"set" if PASSWORD else "not set"}
""")
