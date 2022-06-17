import os
import re
import sys

from flask import Flask, render_template
from loguru import logger

from src import util
from src.api import DockerApiV2

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

if len(sys.argv) > 1:
    URL = sys.argv[1]
    logger.info(f'Using registry URL {URL} from sys.argv')
else:
    URL = os.environ['REGISTRY_URL']
    logger.info(f'Using registry URL {URL} from env REGISTRY_URL')

registry = DockerApiV2(
    URL,
    username=os.environ.get('REGISTRY_USERNAME'),
    password=os.environ.get('REGISTRY_PASSWORD')
)
context = {
    'site': re.sub('https?://', '', URL)
}

@app.route('/')
def list_repositories():
    repositories = registry.repositories()
    return render_template('repositories.html', context=context, repositories=repositories)

@app.route('/repo/<repo>')
def list_tags(repo: str):
    tags = registry.tags(repo)
    return render_template('tags.html', context=context, tags=tags, repo=repo)

@app.route('/image/<repo>/<tag>')
def tag_history(repo, tag):
    # history = (config + layers) aka image
    history = registry.history(repo, tag)
    history['size_h'] = util.bytes_str(history['size'])
    for layer in history['layers']:
        layer['size_h'] = util.bytes_str(layer['size'])
    return render_template('history.html',
        context=context,
        history=history,
        repo=repo,
        tag=tag
    )

def main():
    app.run(host="0.0.0.0")

if __name__ == '__main__':
    main()
