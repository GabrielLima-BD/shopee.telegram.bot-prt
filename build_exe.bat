@echo off
echo ========================================
echo   Compilando Sistema Shopee Telegram
echo ========================================
echo.

REM Ativa o ambiente virtual
call .\venv\Scripts\activate.bat

REM Remove builds anteriores
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec

echo.
echo [1/3] Compilando com PyInstaller...
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Shopee-Telegram-BOT" ^
    --icon=NONE ^
    --add-data "app;app" ^
    --add-data "scripts;scripts" ^
    --hidden-import=tkinter ^
    --hidden-import=telegram ^
    --hidden-import=telegram.ext ^
    --hidden-import=requests ^
    --hidden-import=PIL ^
    --hidden-import=dotenv ^
    --collect-all telegram ^
    --collect-all python-telegram-bot ^
    main_app.py

echo.
echo [2/3] Criando pasta Aplicativo...
if not exist "Aplicativo" mkdir Aplicativo

echo.
echo [3/3] Movendo executavel...
move /y "dist\Shopee-Telegram-BOT.exe" "Aplicativo\Shopee-Telegram-BOT.exe"

echo.
echo ========================================
echo   COMPILACAO CONCLUIDA COM SUCESSO!
echo ========================================
echo.
echo Executavel criado em: Aplicativo\Shopee-Telegram-BOT.exe
echo.
echo IMPORTANTE: 
echo - Crie um arquivo .env na mesma pasta do .exe
echo - As pastas data, downloads e processed serao criadas automaticamente
echo.
pause
