# 🎬 Sistema Shopee Telegram Bot

Sistema automatizado para processamento e distribuição de vídeos via Telegram, com upscale automático de resolução, gerenciamento de banco de dados dual e interface gráfica moderna.

## 📋 Índice

- [Características](#-características)
- [Requisitos](#-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Características

### 🤖 Bot do Telegram
- Recebe vídeos via bot do Telegram automaticamente
- Suporta URLs diretas (.mp4) e file_id do Telegram
- Processa links de produtos e descrições

### 🎥 Processamento de Vídeo
- **Upscale automático garantido** para resolução mínima de 720p
- Suporta Video2X e FFmpeg
- Validação de qualidade antes do envio
- Três modos de processamento:
  - Processamento individual
  - Processamento por etapas (ideal para 30-40 vídeos)
  - Reprocessamento de falhas

### 💾 Banco de Dados Dual
- **Banco de Vídeos Originais**: Armazena vídeos baixados
- **Banco de Vídeos Processados**: Vídeos upscaled e prontos para envio
- Rastreamento completo de status e tentativas
- Viewer integrado na GUI

### 🖥️ Interface Gráfica Moderna
- Tema escuro otimizado
- Terminal de logs em tempo real
- Indicadores de progresso por etapa (Download → Processamento → Envio)
- Scroll com mouse/touchpad
- Botão de retry individual por vídeo
- Estatísticas de processamento

### 📱 Caption Inteligente
Formato automático no Telegram:
```
Descrição do produto | 720p

https://link-do-produto.com
```

---

## 🔧 Requisitos

### Sistema Operacional
- Windows 10/11 (64-bit)

### Software Necessário
- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **FFmpeg** (instalação automática via script ou manual)
- **Git** ([Download](https://git-scm.com/downloads))

### Opcional
- **Video2X** (para upscale de qualidade superior)

---

## 📥 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/GabrielLima-BD/P---Shopee_Telegram-BOT.git
cd P---Shopee_Telegram-BOT
```

### 2. Crie o Ambiente Virtual

```bash
python -m venv venv
```

### 3. Ative o Ambiente Virtual

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
.\venv\Scripts\activate.bat
```

### 4. Instale as Dependências

```bash
pip install -r requirements.txt
```

### 5. Instale o FFmpeg

**Opção 1: Script Automático (Recomendado)**
```powershell
# Execute como Administrador
.\scripts\install_all.bat
```

**Opção 2: Winget**
```powershell
winget install FFmpeg
```

**Opção 3: Manual**
1. Baixe FFmpeg: https://www.gyan.dev/ffmpeg/builds/
2. Extraia para `C:\ffmpeg`
3. Adicione `C:\ffmpeg\bin` ao PATH do sistema

---

## ⚙️ Configuração

### 1. Configure o Bot do Telegram

Crie um arquivo `.env` na raiz do projeto:

```env
# === Bot do Telegram ===
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
TELEGRAM_SEND_TOKEN=seu_token_aqui  # Pode ser o mesmo do BOT_TOKEN

# === Banco de Dados ===
USE_DUAL_DATABASES=true
DB_ORIGINAL_PATH=data/videos_original.db
DB_PROCESSED_PATH=data/videos_processados.db

# === Diretórios ===
DOWNLOAD_DIR=downloads
PROCESSED_DIR=processed

# === Processamento ===
VIDEO_TARGET_MIN_HEIGHT=720
PREFER_VIDEO2X_FIRST=false
TIMEOUT_VIDEO2X_SECONDS=300

# === Modo de Operação ===
ONLY_DOWNLOAD=false
ONLY_VALIDATE=false
ONLY_SEND=false
RETRY_FAILED_ONLY=false

# === FFmpeg (Opcional) ===
FFMPEG_DIR=C:\ffmpeg
```

### 2. Como Obter o Token do Bot

1. Abra o Telegram e procure por **@BotFather**
2. Envie `/newbot` e siga as instruções
3. Copie o token fornecido
4. Cole no `.env` como `TELEGRAM_BOT_TOKEN`

### 3. Como Obter o Chat ID

**Método 1: Via Bot @userinfobot**
1. Procure por **@userinfobot** no Telegram
2. Envie `/start`
3. Copie seu ID

**Método 2: Via API**
1. Envie uma mensagem para seu bot
2. Acesse: `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
3. Procure por `"chat":{"id":123456789}`

### 4. Inicialize os Bancos de Dados

```bash
python scripts/init_dual_databases.py
```

---

## 🚀 Como Usar

### Inicie a Aplicação

```bash
python main_app.py
```

A interface gráfica será aberta automaticamente.

### Modo 1: Processamento Individual (Poucos Vídeos)

1. Clique em **"➕ Adicionar e Processar Vídeos"**
2. Preencha os campos:
   - **Link do Vídeo (.mp4)**: URL direta do vídeo
   - **Link do Produto**: URL da página do produto
   - **Descrição**: Texto curto (ex: "Tênis Nike Air Max")
3. Clique em **"▶️ Processar Todos"**
4. Acompanhe os indicadores:
   - 📥 Download: ◻️ → ⏳ → ✅/❌
   - 🛠️ Processamento: ◻️ → ⏳ → ✅/❌
   - 📤 Envio: ◻️ → ⏳ → ✅/❌

### Modo 2: Processamento por Etapas (30-40 Vídeos)

**Ideal para grandes volumes!**

1. Clique em **"➕➕ Adicionar Vários"** para criar múltiplos cards
2. Preencha todos os vídeos
3. Clique em **"⏭️ Processar por Etapas"**

O sistema executará em 3 fases:
- **Fase 1**: Baixa TODOS os vídeos
- **Fase 2**: Processa/Upscale TODOS
- **Fase 3**: Envia TODOS para o Telegram

### Modo 3: Retry de Falhas

Se algum vídeo falhar:

**Retry Individual:**
- Clique no botão **"↻"** ao lado do vídeo que falhou

**Retry em Lote:**
- Clique em **"🔄 Reprocessar Falhas"** na janela de gerenciamento

### Gerenciamento de Banco de Dados

- **📊 Ver Banco Originais**: Visualiza vídeos baixados
- **📊 Ver Banco Processados**: Visualiza vídeos processados
- **🗑️ Limpar Tudo**: Remove todos os registros (cuidado!)

---

## 📁 Estrutura do Projeto

```
P---Shopee_Telegram-BOT/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configurações do sistema
│   ├── db.py                  # Operações de banco de dados
│   ├── bot_ingest.py          # Bot do Telegram (recepção)
│   ├── simple_processor.py    # Pipeline de processamento
│   ├── video_tools.py         # FFmpeg, Video2X, validações
│   └── gui_manager.py         # Interface gráfica
├── scripts/
│   ├── init_dual_databases.py        # Inicializa DBs
│   ├── update_database_schema.py     # Migração de schema
│   ├── recreate_databases.py         # Recria DBs (perde dados)
│   ├── check_environment.py          # Verifica ambiente
│   ├── install_all.bat               # Instala FFmpeg/Video2X
│   └── install_video2x.ps1           # Script PowerShell
├── data/                      # Bancos de dados SQLite
├── downloads/                 # Vídeos originais baixados
├── processed/                 # Vídeos processados
├── .env                       # Configurações (criar manualmente)
├── requirements.txt           # Dependências Python
├── main_app.py               # Ponto de entrada
└── README.md                 # Este arquivo
```

---

## 🔍 Troubleshooting

### ❌ Erro: "FFmpeg não encontrado"

**Solução 1**: Instale via script automático
```powershell
.\scripts\install_all.bat
```

**Solução 2**: Adicione ao PATH
1. Painel de Controle → Sistema → Configurações Avançadas
2. Variáveis de Ambiente
3. Adicione `C:\ffmpeg\bin` à variável PATH

**Solução 3**: Configure no .env
```env
FFMPEG_DIR=C:\caminho\para\ffmpeg
```

### ❌ Erro: "resolution_too_low" no banco

**Causa**: O upscale falhou

**Solução**:
1. Verifique se FFmpeg está instalado: `ffmpeg -version`
2. Tente reprocessar: Botão **"🔄 Reprocessar Falhas"**
3. Verifique logs para erros específicos

### ❌ Bot não recebe mensagens

**Checklist**:
1. ✅ Token correto no `.env`?
2. ✅ Chat ID correto?
3. ✅ Enviou `/start` para o bot?
4. ✅ Bot está rodando (logs dizem "Bot do Telegram rodando")?

### ❌ Vídeos não são enviados para o Telegram

**Checklist**:
1. ✅ `TELEGRAM_SEND_TOKEN` configurado?
2. ✅ `TELEGRAM_CHAT_ID` correto?
3. ✅ Vídeo está no status "processed" no banco?
4. ✅ Verifique erros nos logs da GUI

### ❌ Erro de permissão no PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ Interface não abre

**Solução**:
1. Verifique se Python 3.10+ está instalado
2. Reinstale dependências: `pip install -r requirements.txt --force-reinstall`
3. Execute: `python scripts/check_environment.py`

---

## 📊 Estatísticas e Monitoramento

A GUI exibe em tempo real:
- ✅ Total de vídeos baixados
- ✅ Total de vídeos processados
- ✅ Total de vídeos enviados
- ✅ Total de falhas

Logs coloridos indicam:
- 🔵 **INFO**: Operações normais
- 🟢 **SUCCESS**: Operações bem-sucedidas
- 🟡 **WARNING**: Avisos não críticos
- 🔴 **ERROR**: Erros que precisam atenção
- 🟣 **PROCESSING**: Processamento em andamento

---

## 🛠️ Scripts Úteis

### Verificar Ambiente
```bash
python scripts/check_environment.py
```

### Recriar Bancos de Dados (⚠️ PERDE DADOS)
```bash
python scripts/recreate_databases.py
```

### Atualizar Schema do Banco
```bash
python scripts/update_database_schema.py
```

---

## 🔐 Segurança

⚠️ **NUNCA** commite o arquivo `.env` para o Git!

O `.gitignore` já está configurado para ignorar:
- `.env`
- `*.db`
- `downloads/`
- `processed/`
- `__pycache__/`
- `venv/`

---

## 📝 Licença

Este projeto é de uso pessoal/educacional.

---

## 🤝 Contribuição

Para contribuir:
1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

---

## 📧 Suporte

Para dúvidas ou problemas:
- Abra uma [Issue](https://github.com/GabrielLima-BD/P---Shopee_Telegram-BOT/issues)
- Entre em contato via Telegram

---

## 🎯 Roadmap

- [ ] Suporte para múltiplos idiomas na GUI
- [ ] Upload direto de vídeos pela interface
- [ ] Scheduler para processamento em horários específicos
- [ ] Dashboard web para monitoramento remoto
- [ ] Suporte para outros bots (Discord, WhatsApp)
- [ ] Compressão inteligente de vídeos
- [ ] Integração com APIs de e-commerce

---

**Desenvolvido com ❤️ para automação de processos**
