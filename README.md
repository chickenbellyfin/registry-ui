# Docker Registry UI

## Features
* Minimal web interface
* Basic Auth

## Run
```
pip install -r requirements.txt

python3 -m src.main <http://registry.url>
```

## Configuration

REGISTRY_URL can also be specified as the CLI argument (see Run section above). The CLI arg will take precedence over the environment variable.

| ENV | Required? | Default | Description |
| --- | --- | --- | --- |
| REGISTRY_URL | **Required** | | URL for docker registry, including http[s]:// |
| REGISTRY_USERNAME | | | Username for Basic Auth. If `REGISTRY_PASSWORD` is not set, will not be used |
| REGISTRY_PASSWORD | | | Password for Basic Auth. Must be set along with `REGISTRY_USERNAME` |
| APP_THEME | | `auto` |CSS theme to use. Must be `light`, `dark`, or `auto`. auto [selects light or dark based on browser settings.](https://watercss.kognise.dev/)


## Docker Build
```
docker build . -t registryui
```

## Docker Run
```
docker run -p 5000:5000 -it registryui http://registry.url
```

docker-compose
```
services:
  registryui:
    image: registryui
    container_name: registryui
    ports:
      - 5000:5000
    environment:
      - REGISTRY_URL=http://registry.url
    restart: unless-stopped
```