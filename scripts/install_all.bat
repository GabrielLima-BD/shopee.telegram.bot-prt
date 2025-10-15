@echo off
setlocal EnableExtensions EnableDelayedExpansion
>nul 2>&1 net session
if %errorlevel% neq 0 (
  echo [ERRO] Rode este script como Administrador.
  pause
  exit /b 1
)
set FF_DIR=C:\ffmpeg
set V2X_DIR=C:\Video2X
set FF_BIN=%FF_DIR%\bin
set V2X_BIN=%V2X_DIR%\bin
if not exist "%FF_DIR%" mkdir "%FF_DIR%"
if not exist "%V2X_DIR%" mkdir "%V2X_DIR%"
if exist "%~dp0install_ffmpeg.bat" (
  call "%~dp0install_ffmpeg.bat"
) else (
  winget install --id=Gyan.FFmpeg -e --source winget
)
if exist "%~dp0install_video2x.ps1" (
  powershell -ExecutionPolicy Bypass -File "%~dp0install_video2x.ps1"
) else (
  if not exist "%V2X_BIN%" mkdir "%V2X_BIN%"
)
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path ^| find /i "Path"') do set SYS_PATH=%%b
set NEED_SAVE=0
echo %SYS_PATH% | find /i "%FF_BIN%" >nul || ( setx /M PATH "%SYS_PATH%;%FF_BIN%" >nul & set NEED_SAVE=1 )
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path ^| find /i "Path"') do set SYS_PATH=%%b
echo %SYS_PATH% | find /i "%V2X_BIN%" >nul || ( setx /M PATH "%SYS_PATH%;%V2X_BIN%" >nul & set NEED_SAVE=1 )
if %NEED_SAVE%==1 ( echo [OK] PATH atualizado. Feche e reabra o terminal. ) else ( echo [OK] PATH ok. )
echo [DONE]
endlocal
exit /b 0
