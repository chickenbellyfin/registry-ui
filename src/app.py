import re

from sanic import Request, Sanic, response
from sanic_ext import render

from src.api import ApiCredentials, DockerApiV2, UnauthorizedApiError
from src.data_fetch import fetch_image_list, fetch_repositories, fetch_tags

THEME_CSS = {
  'light': 'light.min.css',
  'dark': 'dark.min.css',
  'auto': 'water.min.css'
}

def create_app(url: str, registry: DockerApiV2, theme: str, enable_login) -> Sanic:
  app = Sanic('registry-ui')

  # extra context for jinja templates
  site_context = {
    'site': re.sub('https?://', '', url),
    'theme': THEME_CSS[theme]
  }

  def jinja_context(**kwargs):
    return {'context': site_context, **kwargs}

  app.static('/static', 'static')

  if enable_login:
    @app.on_request
    async def extract_auth(request: Request):
      username = request.cookies.get('registry_username')
      password = request.cookies.get('registry_password')    
      request.ctx.creds = ApiCredentials(username, password)
    
    @app.exception(UnauthorizedApiError)
    async def handle_unauthorized(request, exception):
      res = response.redirect('/login')
      del res.cookies['registry_username']
      del res.cookies['registry_password']
      return res

    @app.get('/login')
    async def login(request):
      response = await render('login.html', context=jinja_context())
      return response

    @app.post('/submit_login')
    async def submit_login(request):
      res = response.redirect('/')
      res.cookies['registry_username'] = request.form.get('username')
      res.cookies['registry_password'] = request.form.get('password')
      return res
  else:
    @app.on_request
    async def empty_auth(request: Request):
      request.ctx.creds = None
    
    @app.exception(UnauthorizedApiError)
    async def handle_unauthorized(request, exception):
      return await render('unauthorized.html', context=jinja_context())

  @app.get('/')
  async def list_repositories(request: Request):
    repositories = await fetch_repositories(registry, creds=request.ctx.creds)
    return await render(
      'repositories.html', context=jinja_context(repositories=repositories)
    )

  @app.get('/repo')
  async def list_tags(request: Request):
    repo = request.args.get('repo')
    tags = await fetch_tags(registry, repo, creds=request.ctx.creds)
    return await render('tags.html', context=jinja_context(tags=tags, repo=repo))

  @app.get('/image')
  async def tag_history(request: Request):
    repo = request.args.get('repo')
    tag = request.args.get('tag')
    images =  await fetch_image_list(registry, repo, tag, creds=request.ctx.creds)
    return await render('history.html', context=jinja_context(images=images, repo=repo, tag=tag))

  return app
