@echo off
setlocal EnableDelayedExpansion
title ai_doctor_api

set current_dir_name=%~dp0

cd /d %current_dir_name%
echo ai doctor api start...
python app.py