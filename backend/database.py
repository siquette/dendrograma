"""
database.py — Gerencia a conexão com o PostgreSQL.

Cria o engine (a "ponte" entre Python e Postgres) e fornece sessões
para os endpoints usarem. Cada request HTTP recebe uma sessão própria
que é fechada automaticamente ao final.

Por que SQLAlchemy e não SQL puro?
- Previne SQL injection automaticamente
- Mapeia tabelas para classes Python (models/)
- Gerencia pool de conexões (reuso eficiente)
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings


# Engine — a conexão "raiz" com o banco.
# pool_pre_ping=True testa se a conexão ainda está viva antes de usar.
# Evita erros quando o Postgres reinicia e as conexões antigas morrem.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,          # conexões simultâneas no pool
    max_overflow=20,       # conexões extras em picos de uso
    echo=settings.is_development,  # loga SQL no console em dev
)

# SessionLocal — fábrica de sessões.
# Cada chamada a SessionLocal() cria uma sessão nova.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Base — classe mãe de todos os models (tabelas).
# Os models em models/ herdam dela.
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency injection do FastAPI.
    Cada endpoint que precisa do banco declara: db: Session = Depends(get_db)
    O FastAPI chama essa função, entrega a sessão, e garante que ela
    é fechada ao final — mesmo se der erro.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
