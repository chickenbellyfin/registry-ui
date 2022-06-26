# Docker Registry UI
![Unit Tests](https://github.com/chickenbellyfin/registry-ui/actions/workflows/python-test.yml/badge.svg) ![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/chickenbellyfin/registry-ui)

| | | |
| -- | -- | -- |
| | ![](/static/logo.svg) | |
| ![](/screenshots/indexd.jpg) | ![](/screenshots/tagsd.jpg) | ![](/screenshots/imaged.jpg) |

## Features
* Minimal web interface
* Basic Auth & login
* multi-arch support

Built with python, [sanic](https://sanic.dev), and [water.css](https://watercss.kognise.dev/)

## Run
```
docker run -p 8000:8000 chickenbellyfin/registry-ui -r <http://registry.url>
```

Or, checkout this repo and run:
```
pip install -r requirements.txt

python3 -m src.main -r <http://registry.url>

# If you don't have a registry already, you can use the demo data from this repo:
$ python3 -m src.main -r http://chickenbellyfin.github.io/registry-ui
```

## Configuration

### CLI
CLI args take precendence over environment variables.
```
usage: main.py [-h] [-r REGISTRY] [-l] [-u USERNAME] [-p PASSWORD]

optional arguments:
  -h, --help            show this help message and exit
  -r REGISTRY, --registry REGISTRY
                        Registry URL (with http:// or https://)
  -l, --login           Show a login page for registries which require basic auth.
  -u USERNAME, --username USERNAME
                        Username for registry basic auth
  -p PASSWORD, --password PASSWORD
                        Password for registry basic auth
```
### Environment

| ENV | Required? | Default | Description |
| --- | --- | --- | --- |
| REGISTRY_URL | **Required** | | URL for docker registry, including http[s]:// |
| REGISTRY_USERNAME | | | Username for Basic Auth. If `REGISTRY_PASSWORD` is not set, will not be used **See Authorization section** |
| REGISTRY_PASSWORD | | | Password for Basic Auth. Must be set along with `REGISTRY_USERNAME` **See Authorization section** |
| APP_THEME | | `auto` |CSS theme to use. Must be `light`, `dark`, or `auto`. auto [selects light or dark based on browser settings.](https://watercss.kognise.dev/)
| APP_ENABLE_LOGIN | | `true` | Shows a login page if the registry requires credentials. The credentials are forwarded to the registry with basic auth. **See Authorization section**
| APP_DEBUG | | `true` in development, `false` in docker | Whether to run sanic server in debug mode.

### About Authorization

* The authorization works by simply forwarding username and password in a Basic Auth HTTP header to the API, whether those were set in the server settings or from the user's login cookies.
* If the Regsitry username & password are set using `-u`/`-p` or `REGISTRY_USERNAME`/`REGISTRY_PASSWORD`, the app will **always** try to use those credentials, even if the user has not logged in. If you set `--login` or `APP_ENABLE_LOGIN`, it is recommended to not set the registry username and password. This will force each user to enter the credentials on the login page before getting access.
* It is required to enable HTTPS on any registry which requires Basic Auth.
* It is recommended to enable authorization if your registry is facing the public internet.

This app provides a couple options for authorization but does not provide any security guarantees or enforce any secure practices by the user.

## Docker Build
```
docker build . -t registryui
```

## Docker Run
```
docker run -p 8000:8000 -it registryui http://registry.url
```

docker-compose
```
services:
  registry-ui:
    image: registry-ui
    container_name: registry-ui
    ports:
      - 8000:8000
    environment:
      - REGISTRY_URL=http://registry.url
    restart: unless-stopped
```

## Example: Hosting alongside regsitry with HTTPS & basic auth
It is possible to host the web app at the same URL as the registry using a web server/reverse proxy such as [caddy](https://caddyserver.com/).

This setup will allow you to host a registry at `https://my.registry.url` which allows image push/pull to `my.registry.url/<image>:<tag>`, and shows a web ui with a login page at that url in the browser. The credentials for docker client and for web access will be the same as what is configured in the registry's htpasswd.

docker-compose.yaml:
```
services:
  caddy:
    image: caddy
    container_name: caddy
    restart: unless-stopped
    ports:
      - 80:80
      - 443:443
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - certs-volume:/data

  registry:
    image: registry:2
    container_name: registry
    restart: unless-stopped
    volumes:
      - 'registry-volume:/var/lib/registry'
      - './htpasswd:/auth'
    environment:
    # How to configure registry basic auth
    # https://docs.docker.com/registry/deploying/#native-basic-auth
      - REGSITRY_AUTH=htpasswd
      - REGISTRY_AUTH_HTPASSWD_REALM=Registry Realm
      - REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd

  registry-ui:
    image: chickenbellyfin/registry-ui
    container_name: registry-ui
    restart: unless-stopped
    environment:
      - REGISTRY_URL=https://my.registry.url
      - APP_ENABLE_LOGIN=true

volumes:
  certs-volume:
  registry-volume:
```

Caddyfile:
```
my.registry.url {
  handle /v2* {
    reverse_proxy registry:5000
  }
  reverse_proxy registry-ui:8000
}
```

### Test
```
python3 -m pytest

coverage run && coverage report

# open htmlcov/index.html
coverage html
```

### Push
```
docker buildx build --platform linux/amd64,linux/arm64 --tag chickenbellyfin/registry-ui --push .
```
