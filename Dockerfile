# ============================================
# NEXAS Analytics — Dockerfile
# Build: docker build -t nexas-analytics .
# ============================================

FROM python:3.12-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho dentro do container
WORKDIR /app

# Instalar dependências do sistema (necessárias para psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY backend/ backend/
COPY frontend/ frontend/
COPY scripts/ scripts/
COPY migrations/ migrations/

# Porta da aplicação
EXPOSE 8000

# Comando de inicialização
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
