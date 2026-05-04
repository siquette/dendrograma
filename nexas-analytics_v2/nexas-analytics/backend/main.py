"""
main.py — Ponto de entrada da aplicação FastAPI.

Amarra tudo: cria o app, registra os routers, configura CORS,
e serve os arquivos estáticos do frontend.

Para rodar em desenvolvimento:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

O --reload faz o servidor reiniciar automaticamente quando você edita código.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import engine, Base
from backend.routers import filtros, tree, ingestao

# ============================================
# Configuração de logging
# ============================================
logging.basicConfig(
    level=logging.INFO if settings.is_development else logging.WARNING,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================
# Criar a aplicação FastAPI
# ============================================
app = FastAPI(
    title="NEXAS Analytics",
    description="Dashboard analítico de visualização de associações (Lift Condicional)",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,   # Swagger UI só em dev
    redoc_url="/redoc" if settings.is_development else None,
)

# ============================================
# CORS — quais domínios podem acessar a API
# ============================================
# Em desenvolvimento, permite localhost.
# Em produção, restringe ao domínio do frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Registrar os routers (endpoints)
# ============================================
app.include_router(filtros.router)
app.include_router(tree.router)
app.include_router(ingestao.router)

# ============================================
# Servir arquivos estáticos do frontend
# ============================================
# O FastAPI serve o index.html, CSS e JS diretamente.
# Não precisa de um servidor web separado (nginx, etc.) em dev.
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    logger.info(f"Frontend servido de: {frontend_path}")
else:
    logger.warning(f"Pasta frontend não encontrada: {frontend_path}")


# ============================================
# Eventos de ciclo de vida
# ============================================
@app.on_event("startup")
def on_startup():
    """Roda quando a aplicação inicia."""
    # Cria as tabelas no banco se não existirem
    # Em produção, usar migrations ao invés disso
    Base.metadata.create_all(bind=engine)
    logger.info("NEXAS Analytics iniciado")
    logger.info(f"Ambiente: {settings.app_env}")
    logger.info(f"Docs disponível em: http://localhost:{settings.app_port}/docs")


@app.get("/api/health")
def health_check():
    """Endpoint de saúde — usado pra monitoramento."""
    return {"status": "ok", "version": "0.1.0"}
