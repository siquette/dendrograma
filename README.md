# NEXAS Analytics

Dashboard analítico de visualização de associações (Lift Condicional) para pesquisa de mercado.

## Setup com Pixi (recomendado)

```powershell
# 1. Instalar Pixi (só precisa fazer uma vez)
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"

# 2. Entrar no projeto
cd C:\vanessa\code\nexas-analytics

# 3. Instalar dependências (cria ambiente isolado automaticamente)
pixi install

# 4. Criar o .env
copy .env.example .env

# 5. Ingerir dados
copy C:\vanessa\dados\WORKBOOK_ANALISE_VERSAO_INICIAL_2.xlsx dados\
pixi run ingest "dados\WORKBOOK_ANALISE_VERSAO_INICIAL 2.xlsx" --onda 2025-Q1

# 6. Rodar o servidor
pixi run serve

# 7. Acessar http://localhost:8000
```

### Tasks disponíveis

| Comando | O que faz |
|---------|-----------|
| `pixi run serve` | Inicia o servidor de desenvolvimento (com hot reload) |
| `pixi run serve-prod` | Inicia em modo produção |
| `pixi run ingest "arquivo.xlsx" --onda ID` | Ingere XLSX no banco |
| `pixi run create-db` | Cria/reseta as tabelas do banco |
| `pixi run -e dev test` | Roda os testes |

## Setup alternativo (venv + pip)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m scripts.ingest_cli "dados\arquivo.xlsx" --onda 2025-Q1
uvicorn backend.main:app --reload --port 8000
```

## Estrutura do projeto

```
backend/        → FastAPI (API REST)
frontend/       → HTML + CSS + D3.js (Dendrograma Collapsible Tree)
scripts/        → Ferramentas operacionais (ingestão CLI)
migrations/     → Schema SQL versionado
dados/          → XLSX locais + SQLite (não versionados)
```

Detalhes completos no `PRD_NEXAS_ANALYTICS.md`.

## Stack

- **Ambiente:** Pixi (ou venv + pip como alternativa)
- **Backend:** FastAPI + SQLAlchemy + SQLite (PostgreSQL quando migrar pra produção)
- **Frontend:** HTML + CSS + D3.js v7 (Dendrograma Collapsible Tree)

