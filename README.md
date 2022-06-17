# Docker Registry UI

## Run
```
pip install -r requirements.txt

python3 -m src.main <http://registry.url>
```

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