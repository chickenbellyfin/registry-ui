import re

import jinja2
from sanic import Sanic, response

from src.api import ApiCredentials, DockerApiV2, UnauthorizedApiError
from src.data_fetch import fetch_image_list, fetch_repositories, fetch_tags

THEME_CSS = {
  'light': 'light.min.css',
  'dark': 'dark.min.css',
  'auto': 'water.min.css'
}

def create_app(url: str, registry: DockerApiV2, theme: str, enable_login) -> Sanic:
  app = Sanic('registry-ui')

  # Using jinja directly instead of through sanic-ext because its currently broken (in tests)
  # https://github.com/sanic-org/sanic-ext/issues/85
  jinja_env = jinja2.Environment(
    enable_async=True,
    loader=jinja2.FileSystemLoader("templates"),
    autoescape=jinja2.select_autoescape()
  )

  async def render(template, **kwargs):
    return response.html(await jinja_env.get_template(template).render_async(**kwargs))

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
    response = await render('login.html', context=context)
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
      'repositories.html',
      context=context,
      repositories=repositories
    )

  @app.get('/repo')
  @auth
  async def list_tags(request, creds=None):
    repo = request.args.get('repo')
    tags = await fetch_tags(registry, repo, creds=creds)
    return await render('tags.html',
      context=context,
      tags=tags,
      repo=repo
    )

  @app.get('/image')
  @auth
  async def tag_history(request, creds=None):
    repo = request.args.get('repo')
    tag = request.args.get('tag')
    images =  await fetch_image_list(registry, repo, tag, creds=creds) # registry.history(repo, tag)
    return await render('history.html',
      context=context,
      images=images,
      repo=repo,
      tag=tag
    )

  return app
