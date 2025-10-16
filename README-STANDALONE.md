# 🚀 Shopee Telegram BOT - Standalone

**Executável único que funciona em qualquer lugar!**

---

## 🎯 PARA QUEM VAI USAR (Não é programador)

### O que você recebe:
- ✅ **1 arquivo**: `Shopee-Telegram-BOT.exe` (18 MB)
- ❌ **Não precisa** de Python, .env, pastas ou nada mais!

### Como usar:

1. Copie o `.exe` para qualquer pasta
2. Dê duplo clique
3. Pronto! Pastas serão criadas automaticamente:
   - `downloads/` → Vídeos baixados
   - `processed/` → Vídeos processados
   - `data/` → Banco de dados

### Interface:

A janela mostra:
- **Total**: Vídeos no banco
- **Pendentes**: Aguardando
- **Processados**: Enviados ✅
- **Falhas**: Com erro ❌

### 3 Botões:

1. **Processar Tudo** → Baixa, processa e envia
2. **Apenas Processar** → Usa vídeos já baixados
3. **Reprocessar Falhas** → Tenta de novo os que falharam

> 💡 **Upscale opcional**: Instale FFmpeg em `C:\ffmpeg\` para melhorar qualidade

---

## 🔧 PARA QUEM VAI COMPILAR (Programador)

### Pré-requisitos:
- Python 3.10+
- PyInstaller (`pip install pyinstaller`)

### Passos:

#### 1️⃣ Configure os tokens (UMA VEZ):

```powershell
python configurar_tokens.py
```

Informe:
- **TELEGRAM_BOT_TOKEN** (do @BotFather)
- **TELEGRAM_CHAT_ID** (ID do canal)

#### 2️⃣ Compile:

```powershell
.\build_standalone.bat
```

Ou manualmente:

```powershell
pyinstaller --noconfirm --onefile --windowed `
  --name "Shopee-Telegram-BOT" `
  --add-data "app;app" `
  --hidden-import=tkinter `
  --hidden-import=telegram `
  --hidden-import=telegram.ext `
  --hidden-import=requests `
  --collect-all telegram `
  main_app.py
```

#### 3️⃣ Pegue o .exe:

```
dist\Shopee-Telegram-BOT.exe  ← Este é o arquivo final!
```

### ⚠️ IMPORTANTE:

- **NUNCA** commite `app/config.py` com tokens reais no Git
- Use `.gitignore` para proteger credenciais
- O `.exe` já vem com tokens embutidos (não extraíveis facilmente)

---

## 🔐 Segurança

### Como funciona:
- Tokens são hard-coded no `app/config.py` antes da compilação
- PyInstaller embute tudo no binário `.exe`
- Não é possível extrair tokens facilmente do `.exe`

### Boas práticas:
- ✅ Compile localmente (não use CI/CD público)
- ✅ Distribua apenas para pessoas confiáveis
- ❌ Não compartilhe o `.exe` publicamente
- ❌ Não commite tokens no GitHub

---

## 📁 Estrutura Automática

Quando você executa o `.exe`, ele cria:

```
[Pasta do .exe]/
├── Shopee-Telegram-BOT.exe  ← Você coloca aqui
├── downloads/                ← Criado automaticamente
├── processed/                ← Criado automaticamente
└── data/                     ← Criado automaticamente
    ├── videos_original.db
    └── videos_processados.db
```

---

## 🐛 Solução de Problemas

### ❌ "Nenhum vídeo para processar"

**Causa**: Banco de dados vazio

**Solução**: Adicione vídeos ao `data/videos_original.db` usando script de importação

---

### ❌ Vídeos não chegam no Telegram

**Possíveis causas**:
1. **Tokens incorretos** → Recompile com tokens corretos
2. **Bot não é admin** → Adicione bot como admin do canal
3. **Vídeo muito grande** → Telegram limita a 50 MB

---

### ❌ "FFmpeg não encontrado"

**Causa**: FFmpeg não instalado (opcional)

**Solução**:
1. Baixe: https://ffmpeg.org/download.html
2. Extraia em: `C:\ffmpeg\bin\ffmpeg.exe`
3. Ou adicione ao PATH do Windows

---

### ❌ Qualidade ruim

**Solução**:
- Instale **Video2X** para upscale melhor
- Ou use vídeos já em alta resolução (720p+)

---

## 🚀 Tecnologias

- **Python 3.14** - Linguagem
- **PyInstaller** - Compilação standalone
- **python-telegram-bot** - API Telegram
- **tkinter** - Interface gráfica
- **SQLite** - Banco de dados
- **FFmpeg/Video2X** - Processamento de vídeo

---

## 📝 Changelog

### v2.0 - Standalone (15/out/2025)
- ✅ Compilação standalone sem dependências
- ✅ Tokens embutidos no código
- ✅ Criação automática de pastas
- ✅ Removida dependência de `.env`
- ✅ Scripts de configuração e build

### v1.0 - Inicial
- ✅ Sistema completo com bot
- ✅ Processamento e upscale
- ✅ Interface gráfica
- ✅ Banco de dados dual

---

## 👤 Autor

**Gabriel Lima**
- GitHub: [@GabrielLima-BD](https://github.com/GabrielLima-BD)
- Email: g.delima.ti@gmail.com

---

## 📜 Licença

Uso pessoal. Não redistribuir publicamente.

---

**Feito com ❤️ para facilitar sua vida!**
