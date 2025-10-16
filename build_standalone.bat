@echo off
echo ========================================
echo   COMPILAR SHOPEE TELEGRAM BOT
echo ========================================
echo.

REM Garantir que nenhuma instância do exe esteja aberta e limpar binário travado
taskkill /IM "Shopee-Telegram-BOT.exe" /F >nul 2>&1
if exist "dist\Shopee-Telegram-BOT.exe" (
    del /F /Q "dist\Shopee-Telegram-BOT.exe" >nul 2>&1
)

REM Verificar se tokens foram configurados (somente nas linhas de atribuicao)
findstr /C:"_HARDCODED_BOT_TOKEN: str = \"SEU_TOKEN_AQUI\"" app\config.py >nul
if %ERRORLEVEL% EQU 0 (
    echo [ERRO] Tokens nao configurados! (_HARDCODED_BOT_TOKEN)
    echo.
    echo Execute primeiro: python configurar_tokens.py
    echo.
    pause
    exit /b 1
)
findstr /C:"_HARDCODED_CHAT_ID: str = \"SEU_CHAT_ID_AQUI\"" app\config.py >nul
if %ERRORLEVEL% EQU 0 (
    echo [ERRO] Tokens nao configurados! (_HARDCODED_CHAT_ID)
    echo.
    echo Execute primeiro: python configurar_tokens.py
    echo.
    pause
    exit /b 1
)

echo [OK] Tokens configurados!
echo.
echo Compilando com PyInstaller...
echo.

pyinstaller --noconfirm --onefile --windowed --name "Shopee-Telegram-BOT" --add-data "app;app" --hidden-import=tkinter --hidden-import=telegram --hidden-import=telegram.ext --hidden-import=requests --collect-all telegram main_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Compilacao falhou!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   COMPILACAO CONCLUIDA!
echo ========================================
echo.
echo O executavel esta em: dist\Shopee-Telegram-BOT.exe
echo.
echo PRONTO PARA DISTRIBUIR!
echo - Nao precisa de .env
echo - Nao precisa de pastas
echo - Funciona em qualquer Windows
echo.
echo As pastas downloads/, processed/ e data/ serao criadas
echo automaticamente onde o .exe for executado.
echo.
pause
