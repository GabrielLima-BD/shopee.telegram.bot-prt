@echo off
echo ========================================
echo   DIAGNOSTICO - Shopee Telegram BOT
echo ========================================
echo.

REM Detectar diretório do script
set SCRIPT_DIR=%~dp0
echo Diretorio do script: %SCRIPT_DIR%

REM Verificar se .env existe
if exist "%SCRIPT_DIR%.env" (
    echo [OK] Arquivo .env encontrado!
    echo.
    echo === CONTEUDO DO .ENV ===
    type "%SCRIPT_DIR%.env"
    echo.
    echo === FIM DO .ENV ===
) else (
    echo [ERRO] Arquivo .env NAO encontrado em: %SCRIPT_DIR%
    echo.
    echo CRIE O ARQUIVO .env NESTA PASTA!
)

echo.
echo ========================================
echo   Pressione qualquer tecla para sair
echo ========================================
pause >nul
