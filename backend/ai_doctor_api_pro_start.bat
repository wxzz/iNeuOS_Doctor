@echo off
setlocal

REM Start production WSGI server (waitress)
cd /d "%~dp0"
waitress-serve --listen=0.0.0.0:5000 app:app

endlocal
