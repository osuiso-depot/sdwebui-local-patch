@echo off

set PYTHON=
set GIT=
set VENV_DIR=
set COMMANDLINE_ARGS=--skip-install --no-download-sd-model --xformers --force-enable-xformers --configpresets-dir "C:\Users\2021NSAPU\Documents\GitHub\MySDWEBUI_config_private"
REM set COMMANDLINE_ARGS=--no-download-sd-model --xformers --force-enable-xformers --configpresets-dir "C:\Users\2021NSAPU\Documents\GitHub\MySDWEBUI_config_private"

call webui.bat
