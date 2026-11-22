@echo off
chcp 65001 >nul
title Adam Desktop
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto run
set "PY=py -3"
where py >nul 2>nul
if not errorlevel 1 goto mkvenv
set "PY=python"
where python >nul 2>nul
if not errorlevel 1 goto mkvenv
echo Python nao encontrado. Instalando o Python 3.12 pelo winget...
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
echo.
echo Python instalado. Feche esta janela e abra o Iniciar-Adam.bat de novo.
pause
exit /b
:mkvenv
echo Preparando o Adam Desktop pela primeira vez...
%PY% -m venv .venv
if errorlevel 1 (
  echo Falha ao criar o ambiente Python.
  pause
  exit /b
)
:run
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r dependencias.txt
".venv\Scripts\python.exe" adam_desktop.py
pause
