# Shopee Telegram Bot

README profissional em Português — instruções essenciais para instalar, configurar e executar o bot Telegram.

## Descrição
- Projeto: bot Telegram para ingestão/monitoramento de vídeos e automações relacionadas à Shopee.
- Objetivo: fornecer um núcleo funcional do bot com scripts de manutenção e instruções mínimas para execução.

## Status atual
- Branch principal: `main`
- Este branch contém apenas os arquivos essenciais para execução do bot (`app/`, `main_app.py`, `run_bot_only.py`, `requirements.txt`, `scripts/`, `tools/`).

## Sumário
- Requisitos
- Instalação
- Configuração
- Execução
- Scripts úteis
- Logs e troubleshooting
- Empacotamento (opcional)
- Recuperar arquivos removidos (caso necessário)
- Estrutura do repositório
- Contribuição

---

## Requisitos
- Python 3.8+ (recomendado 3.10+)
- Dependências listadas em `requirements.txt`
- Token do Bot Telegram
- (Opcional) Banco de dados configurado conforme `app/config.py`

## Instalação (rápida)
1. Crie e ative um ambiente virtual (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instale dependências:

```powershell
pip install -r requirements.txt
```

## Configuração
- Copie `app/config.py.template` para `app/config.py` e preencha as chaves necessárias (ex.: `TELEGRAM_TOKEN`, `DATABASE_URL`, outras variáveis de ambiente usadas pelo projeto).
- Como alternativa, rode o script interativo `configurar_tokens.py` para inserir tokens localmente.

Exemplo (editar `app/config.py`):
```py
TELEGRAM_TOKEN = "seu_token_aqui"
DATABASE_URL = "sqlite:///data/db.sqlite3"
# demais configurações...
```

## Execução
- Para rodar o aplicativo completo (GUI + backend, se aplicável):

```powershell
python main_app.py
```

- Apenas o bot (modo headless):

```powershell
python run_bot_only.py
```

## Scripts úteis
- `scripts/check_environment.py` — valida pré-requisitos do ambiente
- `scripts/init_dual_databases.py` — inicializa bases (se aplicável)
- `scripts/recreate_databases.py` — recria bancos de dados de desenvolvimento
- `scripts/update_database_schema.py` — atualiza esquema do DB
- `tools/test_telegram.py` — utilitário para testar recebimento/envio de mensagens

## Logs e troubleshooting
- Logs e níveis de log são controlados por configurações em `app/config.py`.
- Erros comuns:
  - Token inválido: verifique `TELEGRAM_TOKEN`.
  - Conexão ao banco: valide `DATABASE_URL` e permissões.

## Empacotamento / Build (opcional)
- Para empacotar como executável, recomendamos `pyinstaller`:

```powershell
pip install pyinstaller
pyinstaller --onefile main_app.py
```

> Observação: scripts de build antigos e documentação auxiliares foram removidos para manter o repositório enxuto. Eles podem ser recuperados no histórico Git se necessário.

## Recuperar arquivos removidos
Os arquivos deletados estão no histórico do Git e podem ser recuperados com:

```powershell
# ver histórico
git log --stat
# restaurar arquivo de commit anterior
git checkout <commit> -- path/to/file
```

## Estrutura principal do repositório
- `app/` — código-fonte do bot: módulos de configuração (`config.py`), persistência (`db.py`), processamento, etc.
- `main_app.py` — ponto de entrada principal
- `run_bot_only.py` — inicia somente o bot
- `requirements.txt` — dependências Python
- `scripts/` — scripts de manutenção e DB
- `tools/` — utilitários e testes

## Contribuição
- Abra uma issue para relatar bugs ou solicitar funcionalidades.
- Para contribuir com código: fork, nova branch, PR com descrição clara e testes.

## Licença
- Não há licença explícita neste repositório. Se desejar, adicione um arquivo `LICENSE` com a licença escolhida (ex.: `MIT`).

---

Se precisar, posso:
- ajustar o conteúdo do `README.md` (mais detalhes técnicos, exemplos de config, screenshots etc.),
- adicionar um `CONTRIBUTING.md` ou `LICENSE`.

Arquivo gerado automaticamente pelo assistente a pedido do mantenedor.
