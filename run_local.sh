#!/bin/bash

if [ ! -d "venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
python -m src.main -r http://chickenbellyfin.github.io/registry-ui -n registry-ui
