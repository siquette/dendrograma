# NEXAS Analytics

Dashboard analítico de visualização de associações (Lift Condicional) para pesquisa de mercado.

## Quick Start (com Docker)

```bash
# 1. Clonar e entrar no projeto
cd C:\vanessa\code\nexas-analytics

# 2. Criar o .env
copy .env.example .env

# 3. Subir banco + aplicação
docker-compose up

# 4. Em outro terminal, ingerir os dados
docker-compose exec app python -m scripts.ingest_cli /dados/arquivo.xlsx --onda 2025-Q1

# 5. Acessar
# Dashboard: http://localhost:8000
# API docs:  http://localhost:8000/docs
```

## Quick Start (sem Docker)

```bash
# 1. Criar ambiente virtual
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/Mac

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar banco
# Instalar PostgreSQL e criar o banco 'nexas'
# Editar .env com a URL de conexão

# 4. Criar tabelas
psql -U nexas -d nexas -f migrations/001_create_tables.sql

# 5. Ingerir dados
python -m scripts.ingest_cli dados/arquivo.xlsx --onda 2025-Q1

# 6. Rodar o servidor
uvicorn backend.main:app --reload --port 8000

# 7. Acessar http://localhost:8000
```

## Estrutura do projeto

```
backend/        → FastAPI (API REST)
frontend/       → HTML + CSS + D3.js (dashboard)
scripts/        → Ferramentas operacionais (ingestão CLI)
migrations/     → Schema SQL versionado
dados/          → XLSX locais (não versionados)
```

Detalhes completos no `PRD_NEXAS_ANALYTICS.md`.

## Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** HTML + CSS + D3.js v7
- **Deploy:** Docker (container único)
