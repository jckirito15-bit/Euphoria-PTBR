@echo off
setlocal
cd /d "%~dp0.."
set "PY=%CD%\renpy-sdk\lib\py3-windows-x86_64\python.exe"
set "RENPY_PATH_TO_SAVES=%CD%\trabalho\infra\saves"
set "PROJ=%CD%\renpy\euphoria"
if /i "%~1"=="exemplo" (
  python tools\preparar_infra.py teste
  if errorlevel 1 exit /b 1
  set "PROJ=%CD%\trabalho\infra\teste"
)
python tools\preparar_update.py "%PROJ%"
if errorlevel 1 exit /b 1
"%PY%" tools\gerar_chave_update.py "%PROJ%"
if errorlevel 1 exit /b 1
"%PY%" "%CD%\renpy-sdk\renpy.py" "%CD%\renpy-sdk\launcher" distribute "%PROJ%" --package gameonly --destination "%CD%\saida\renpy-dados"
exit /b %errorlevel%
