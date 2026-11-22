#!/usr/bin/env bash
# Builds AdamSetup.exe (Windows, no Python needed) from Linux with NSIS + Python embeddable.
set -euo pipefail
cd "$(dirname "$0")"
PYV=3.12.10
rm -rf stage wheels && mkdir -p stage/python wheels
curl -sSL -o /tmp/pyembed.zip "https://www.python.org/ftp/python/$PYV/python-$PYV-embed-amd64.zip"
python3 -c "import zipfile; zipfile.ZipFile('/tmp/pyembed.zip').extractall('stage/python')"
printf 'python312.zip\n.\nLib\\\\site-packages\nimport site\n' > stage/python/python312._pth
pip wheel -q --no-deps -w wheels pyautogui==0.9.54 pymsgbox pytweening pyscreeze pygetwindow pyrect mouseinfo pyperclip
pip download -q --no-deps --only-binary=:all: --platform win_amd64 --python-version 3.12 --implementation cp -d wheels \
  pillow requests urllib3 idna certifi charset_normalizer truststore
python3 -c "import glob,zipfile; [zipfile.ZipFile(w).extractall('stage/python/Lib/site-packages') for w in glob.glob('wheels/*.whl')]"
cp ../desktop/adam_desktop.py stage/
python3 -c "import sys; t=open('../desktop/LEIA-ME.txt',encoding='utf-8').read().replace(chr(10),chr(13)+chr(10)); open('stage/LEIA-ME.txt','w',encoding='utf-8',newline='').write(t)"
python3 -c "open('stage/server.txt','w').write('ADAMSRV:' + 'X'*8 + ' '*292)"
makensis -V2 installer.nsi
rm -rf stage wheels
ls -la AdamSetup.exe
