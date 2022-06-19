# registry-ui scripts

## make_static_api.py

Creates a static version of the docker registry API for testing/demo.

#### Instructions
Requirements: docker, python w/ requests library

1. Checkout an new copy of this repo and switch to gh-pages branch
```
# (from registry-ui/)
git clone https://github.com/chickenbellyfin/registry-ui.git ../registry-ui-gh-pages
cd ../registry-ui-gh-pages && git checkout gh-pages
```

2. Run `python3 scripts/make_static_api.py` from the original repo. It will try to cd to `../registry-ui-gh-pages`

3. To use the static output, run `python3 http.server 5000` from `registry-ui-gh-pages`

4. Run registry-ui with the static version as the registry url
```
python3 -m src.main -r http://localhost:5000
```

5. If everything looks good, push to the `gh-pages` branch