#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --disable-pip-version-check -r dependencias.txt
.venv/bin/python adam_desktop.py
