@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ============================================================
echo   INSTALADOR COMPLETO - Shopee Telegram Bot
echo ============================================================
echo.
echo Este script irá:
echo   1. Instalar FFmpeg 8.0 via WinGet
echo   2. Configurar FFmpeg no PATH do sistema
echo   3. Instalar Video2X (opcional)
echo   4. Criar estrutura de pastas e bancos de dados
echo   5. Verificar Python e dependências
echo ============================================================
echo.

:: Verificar privilégios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  ERRO: Este script precisa de privilégios de Administrador!
    echo    Execute este arquivo como Administrador.
    echo.
    pause
    exit /b 1
)

:: ===========================================================
:: ETAPA 1: Instalar FFmpeg via WinGet
:: ===========================================================
echo.
echo ============================================================
echo [1/5] Instalando FFmpeg 8.0 via WinGet...
echo ============================================================
echo.

winget list --id Gyan.FFmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg já está instalado!
    echo    Se desejar reinstalar, desinstale manualmente primeiro.
) else (
    echo 📦 Instalando FFmpeg...
    winget install --id Gyan.FFmpeg -e --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo ❌ Falha ao instalar FFmpeg via WinGet
        echo    Por favor, instale manualmente: https://www.gyan.dev/ffmpeg/builds/
        pause
        exit /b 1
    )
    echo ✅ FFmpeg instalado com sucesso!
)

:: ===========================================================
:: ETAPA 2: Configurar PATH do sistema para FFmpeg
:: ===========================================================
echo.
echo ============================================================
echo [2/5] Configurando FFmpeg no PATH do sistema...
echo ============================================================
echo.

:: Procurar o diretório de instalação do FFmpeg
set "FFMPEG_BASE=%LocalAppData%\Microsoft\WinGet\Packages"
set "FFMPEG_BIN="

for /d %%D in ("%FFMPEG_BASE%\Gyan.FFmpeg*") do (
    for /d %%S in ("%%D\ffmpeg-*") do (
        if exist "%%S\bin\ffmpeg.exe" (
            set "FFMPEG_BIN=%%S\bin"
            goto :found_ffmpeg
        )
    )
)

:found_ffmpeg
if "%FFMPEG_BIN%"=="" (
    echo ⚠️  AVISO: Não foi possível localizar o diretório FFmpeg automaticamente
    echo    O FFmpeg foi instalado, mas você precisa adicionar ao PATH manualmente.
    echo.
    echo    Caminho esperado: %FFMPEG_BASE%\Gyan.FFmpeg_*\ffmpeg-*\bin
    echo.
) else (
    echo 📂 FFmpeg encontrado em: %FFMPEG_BIN%
    
    :: Verificar se já está no PATH
    echo %PATH% | findstr /I /C:"%FFMPEG_BIN%" >nul
    if %errorlevel% equ 0 (
        echo ✅ FFmpeg já está no PATH do sistema!
    ) else (
        echo 🔧 Adicionando FFmpeg ao PATH do sistema...
        setx PATH "%PATH%;%FFMPEG_BIN%" /M >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ FFmpeg adicionado ao PATH com sucesso!
            echo    ⚠️  IMPORTANTE: Reinicie o terminal/cmd para aplicar as mudanças
        ) else (
            echo ⚠️  AVISO: Não foi possível adicionar ao PATH automaticamente
            echo    Adicione manualmente este caminho ao PATH: %FFMPEG_BIN%
        )
    )
)

:: Testar FFmpeg
echo.
echo 🧪 Testando FFmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg encontrado no PATH atual!
    ffmpeg -version | findstr "ffmpeg version"
) else (
    echo ⚠️  FFmpeg não está disponível no PATH atual
    echo    Execute 'refreshenv' ou reinicie o terminal
)

:: ===========================================================
:: ETAPA 3: Instalar Video2X (OPCIONAL)
:: ===========================================================
echo.
echo ============================================================
echo [3/5] Video2X (Opcional - AI Upscaling)
echo ============================================================
echo.
echo O Video2X é usado para upscaling com IA (melhora qualidade).
echo Esta etapa é OPCIONAL e pode demorar.
echo.
set /p INSTALL_VIDEO2X="Deseja instalar Video2X? (S/N): "

if /i "%INSTALL_VIDEO2X%"=="S" (
    echo.
    echo 📦 Instalando Video2X via WinGet...
    winget install --id K4YT3X.Video2X -e --accept-package-agreements --accept-source-agreements
    if %errorlevel% equ 0 (
        echo ✅ Video2X instalado com sucesso!
    ) else (
        echo ⚠️  Falha ao instalar Video2X
        echo    Você pode instalá-lo manualmente depois: https://github.com/k4yt3x/video2x
    )
) else (
    echo ⏭️  Pulando instalação do Video2X
)

:: ===========================================================
:: ETAPA 4: Criar estrutura de pastas e bancos de dados
:: ===========================================================
echo.
echo ============================================================
echo [4/5] Criando estrutura de pastas e bancos de dados...
echo ============================================================
echo.

:: Criar pastas necessárias
echo 📁 Criando pastas...
if not exist "data" mkdir data
if not exist "downloads" mkdir downloads
if not exist "processed" mkdir processed
echo ✅ Pastas criadas: data, downloads, processed

:: Inicializar bancos de dados
echo.
echo 🗄️  Inicializando bancos de dados...
python scripts\init_dual_databases.py
if %errorlevel% equ 0 (
    echo ✅ Bancos de dados criados com sucesso!
) else (
    echo ⚠️  Falha ao criar bancos de dados
    echo    Execute manualmente: python scripts\init_dual_databases.py
)

:: ===========================================================
:: ETAPA 5: Verificar Python e dependências
:: ===========================================================
echo.
echo ============================================================
echo [5/5] Verificando Python e dependências...
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo    Instale Python 3.10+ de https://www.python.org/
    pause
    exit /b 1
)

echo ✅ Python encontrado:
python --version

echo.
echo 📦 Verificando dependências do projeto...
if exist "requirements.txt" (
    echo 🔧 Instalando/verificando pacotes do requirements.txt...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo ✅ Dependências instaladas com sucesso!
    ) else (
        echo ⚠️  Falha ao instalar dependências
        echo    Execute manualmente: pip install -r requirements.txt
    )
) else (
    echo ⚠️  Arquivo requirements.txt não encontrado!
)

:: ===========================================================
:: FINALIZAÇÃO
:: ===========================================================
echo.
echo ============================================================
echo   INSTALAÇÃO CONCLUÍDA! ✅
echo ============================================================
echo.
echo 📋 Resumo:
echo   • FFmpeg: Instalado via WinGet
echo   • PATH: Configurado (reinicie terminal se necessário)
echo   • Video2X: %INSTALL_VIDEO2X%
echo   • Estrutura: Pastas e bancos criados
echo   • Python: Dependências instaladas
echo.
echo 🚀 Próximos passos:
echo   1. Configure os tokens em 'configurar_tokens.py'
echo   2. Execute o bot: python main_app.py
echo   3. Ou compile: pyinstaller Shopee-Telegram-BOT.spec
echo.
echo ⚠️  LEMBRE-SE: Se FFmpeg não funcionar, reinicie o terminal!
echo.
pause
