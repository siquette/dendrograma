# NEXAS Analytics

Dashboard analítico de visualização de associações (Lift Condicional) para pesquisa de mercado.

## Setup local (SQLite + Dendrograma)

```powershell
# 1. Entrar no projeto
cd C:\vanessa\code\nexas-analytics

# 2. Criar ambiente virtual Python
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar o .env
copy .env.example .env
# Garantir que DATABASE_URL=sqlite:///dados/nexas.db

# 5. Ingerir dados
copy C:\vanessa\dados\WORKBOOK_ANALISE_VERSAO_INICIAL_2.xlsx dados\
python -m scripts.ingest_cli dados\WORKBOOK_ANALISE_VERSAO_INICIAL_2.xlsx --onda 2025-Q1

# 6. Rodar o servidor
uvicorn backend.main:app --reload --port 8000

# 7. Acessar http://localhost:8000
```

Obs: Esse fluxo usa **SQLite** (banco em arquivo) em vez de PostgreSQL, pra simplificar a instalação. Zero config, já funciona.

## Estrutura do projeto

```
backend/        → FastAPI (API REST)
frontend/       → HTML + CSS + D3.js (Dendrograma)
scripts/        → Ferramentas operacionais (ingestão CLI)
migrations/     → Schema SQL versionado
dados/          → XLSX locais + SQLite (não versionados)
```

Detalhes completos no `PRD_NEXAS_ANALYTICS.md`.

## Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite (PostgreSQL quando migrar pra produção)
- **Frontend:** HTML + CSS + D3.js v7 (Dendrograma Collapsible Tree)

