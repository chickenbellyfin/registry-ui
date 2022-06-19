"""
Creates a 'static' version of the docker registry API
This is accomplished by starting a local docker registry, adding a bunch of images to it, and
dumping all of the API responses in ../registry-ui-gh-pages (this repo with gh-pages branch checked out)
"""
import os
import requests
import shutil

OUTPUT_DIR="../registry-ui-gh-pages"
SOURCE_REGISTRY = 'http://localhost:5000'

# Images were picked because they are all small, mostly < 30MB
IMAGES = [
  'alpine:latest',
  'alpine:3.16',
  'alpine:3',
  'ubuntu:latest',
  'ubuntu:rolling',
  'redis:latest',
  'redis:bullseye',
  'redis:alpine',
  'redis:7.02',
  'busybox:latest',
  'busybox:glibc',
  'busybox:stable',
  'busybox:unstable',
  'busybox:unstable-musl',
  'traefik:latest',
  'traefik:v2.7',
  'hello-world:latest',
  'hello-world:latest',
  'registry:latest',
  'registry:2.8.1',
  'registry:2.7.1',
  'registry:2.7',
  'registry:2.6.2',
  'registry:2.6',
  'registry:2.5',
  'bash:devel-alpine3.15',
  'bash:devel',
  'bash:latest',
  'bash:rc'
]

# switch to gh-pages repo
os.chdir(OUTPUT_DIR)
if os.path.exists('v2'):
  print('Removing existing v2/')
  shutil.rmtree('v2')

def get(path: str):
  """ Make API call to registry and dump the response to a file before returning"""
  assert '..' not in path and path.startswith('/')
  relative_path = path[1:] # remove leading /
  url = SOURCE_REGISTRY + path

  print(f'Saving {url} => {os.path.abspath(relative_path)}')
  result = requests.get(url, headers={
    'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
  })

  dir, file = os.path.split(path[1:])
  os.makedirs(dir, exist_ok=True)

  with open(relative_path, 'w') as f:
    f.write(result.text)

  return result.json()


# start a local registry and add images to it
os.system('docker rm -f registryui-test')
os.system('docker run --name registryui-test -d -p 5000:5000 registry')

for image in IMAGES:
  os.system(f'docker pull {image} && docker tag {image} localhost:5000/{image}')
  os.system(f'docker push localhost:5000/{image}')

# Crawl the registry and save the API responses
catalog = get('/v2/_catalog')['repositories']

for repo in catalog:
  tags = get(f'/v2/{repo}/tags/list')['tags']

  for tag in tags:
    manifest = get(f'/v2/{repo}/manifests/{tag}')
    print(manifest.keys())
    digest = manifest['config']['digest']
    get(f'/v2/{repo}/blobs/{digest}')

# Stop the registry
os.system('docker kill registryui-test')
