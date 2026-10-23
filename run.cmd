@echo off
setlocal
cd /d "%~dp0"

REM ---------------------------------------------------------------
REM  CHARLA DE DISPENSACION HOSPITALARIA (HGPS) - lanzador local
REM    run.cmd            -> http://127.0.0.1:8501
REM    run.cmd 8600       -> otro puerto
REM    run.cmd 8501 lan   -> accesible desde la red local (charla)
REM ---------------------------------------------------------------

set "PORT=8501"
set "ADDR=127.0.0.1"
if not "%~1"=="" set "PORT=%~1"
if /i "%~2"=="lan" set "ADDR=0.0.0.0"

if exist "%~dp0.pylibs" set "PYTHONPATH=%~dp0.pylibs"

set "PY=python"

echo.
echo   CHARLA DE DISPENSACION HOSPITALARIA - HGPS
echo   Abre:  http://127.0.0.1:%PORT%
if /i "%~2"=="lan" echo   Red local: usa la IP de este equipo en el puerto %PORT%
echo   Deten con Ctrl+C
echo.

"%PY%" -m streamlit run "%~dp0app.py" --server.port %PORT% --server.address %ADDR% --server.headless true

if errorlevel 1 (
    echo.
    echo No se pudo iniciar. Instala las dependencias con:
    echo     pip install -r requirements.txt
    pause
)
endlocal
