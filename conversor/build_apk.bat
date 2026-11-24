@echo off
setlocal
cd /d "%~dp0.."
if not defined JAVA_HOME set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot"
set "PATH=%JAVA_HOME%\bin;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "GRADLE_USER_HOME=%CD%\trabalho\infra\gradle"
set "RENPY_PATH_TO_SAVES=%CD%\trabalho\infra\saves"
set "PY=%CD%\renpy-sdk\lib\py3-windows-x86_64\python.exe"
if not exist "%PY%" (
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\instalar_renpy.ps1
  if errorlevel 1 exit /b 1
)
if not exist "%CD%\android-sdk\platforms\android-36\android.jar" (
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\instalar_renpy.ps1
  if errorlevel 1 exit /b 1
)
set "TIPO=completo"
set "PROJ=%CD%\renpy\euphoria"
>renpy-sdk\rapt\sdk.txt echo %CD%\android-sdk
if not exist "%PROJ%\android.keystore" (
  "%JAVA_HOME%\bin\keytool.exe" -genkeypair -keystore "%PROJ%\android.keystore" -alias android -keyalg RSA -keysize 2048 -keypass android -storepass android -dname "CN=Euphoria PT-BR" -validity 20000
  if errorlevel 1 exit /b 1
)
if not exist "%PROJ%\bundle.keystore" copy /y "%PROJ%\android.keystore" "%PROJ%\bundle.keystore" >nul
"%PY%" "%CD%\renpy-sdk\renpy.py" "%PROJ%" lint
if errorlevel 1 exit /b 1
"%PY%" "%CD%\renpy-sdk\renpy.py" "%CD%\renpy-sdk\launcher" android_build "%PROJ%" --destination "%CD%\saida\renpy-%TIPO%"
if errorlevel 1 exit /b 1
python tools\finalizar_apk.py %TIPO%
exit /b %errorlevel%
