import re

from flask import Flask, render_template

from src.api import DockerApiV2
from src import util

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

URL = 'http://registry.server.local'
registry = DockerApiV2(URL)

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
    app.run()

if __name__ == '__main__':
    main()
