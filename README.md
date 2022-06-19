# Docker Registry UI
| | | |
| -- | -- | -- |
| ![](/screenshots/indexd.jpg) | ![](/screenshots/tagsd.jpg) | ![](/screenshots/imaged.jpg) |
| ![](/screenshots/indexl.jpg) | ![](/screenshots/tagsl.jpg) | ![](/screenshots/imagel.jpg) |

## Features
* Minimal web interface
* Basic Auth

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
usage: main.py [-h] [-r REGISTRY] [-u USERNAME] [-p PASSWORD]

optional arguments:
  -h, --help            show this help message and exit
  -r REGISTRY, --registry REGISTRY
                        Registry URL (with http:// or https://)
  -u USERNAME, --username USERNAME
                        Username for registry basic auth
  -p PASSWORD, --password PASSWORD
                        Password for registry basic auth
```
### Environment

| ENV | Required? | Default | Description |
| --- | --- | --- | --- |
| REGISTRY_URL | **Required** | | URL for docker registry, including http[s]:// |
| REGISTRY_USERNAME | | | Username for Basic Auth. If `REGISTRY_PASSWORD` is not set, will not be used |
| REGISTRY_PASSWORD | | | Password for Basic Auth. Must be set along with `REGISTRY_USERNAME` |
| APP_THEME | | `auto` |CSS theme to use. Must be `light`, `dark`, or `auto`. auto [selects light or dark based on browser settings.](https://watercss.kognise.dev/)
| APP_DEBUG | | `true` in development, `false` in docker | Whether to run sanic server in debug mode.



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
  registryui:
    image: registryui
    container_name: registryui
    ports:
      - 8000:8000
    environment:
      - REGISTRY_URL=http://registry.url
    restart: unless-stopped
```