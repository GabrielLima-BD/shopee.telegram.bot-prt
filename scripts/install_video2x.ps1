Param(
    [string]$InstallDir = "C:\\Video2X\\bin"
)

Write-Host "[INFO] Instalando Video2X em $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
# Exemplo mínimo: o usuário pode colocar manualmente o binário nesta pasta.
# Opcionalmente, baixar release oficial (descomentando e ajustando URL):
# $releaseUrl = "https://github.com/k4yt3x/video2x/releases/latest/download/video2x.exe"
# Invoke-WebRequest -Uri $releaseUrl -OutFile (Join-Path $InstallDir "video2x.exe")
Write-Host "[OK] Pasta preparada em $InstallDir"
