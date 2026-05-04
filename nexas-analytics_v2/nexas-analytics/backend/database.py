"""
database.py — Gerencia a conexão com o banco de dados.

Suporta SQLite (desenvolvimento) e PostgreSQL (produção).
A diferença entre os dois é só a URL no .env:
  - SQLite:     sqlite:///dados/nexas.db
  - PostgreSQL: postgresql://user:pass@host:5432/nexas

O SQLAlchemy abstrai o resto — o mesmo código Python funciona nos dois.

Por que SQLAlchemy e não SQL puro?
- Previne SQL injection automaticamente
- Mapeia tabelas para classes Python (models/)
- Gerencia pool de conexões (reuso eficiente)
"""

from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from backend.config import settings


def _build_engine():
    """
    Cria o engine correto baseado na URL do banco.
    SQLite e PostgreSQL precisam de configurações diferentes.
    """
    url = settings.database_url
    is_sqlite = url.startswith("sqlite")

    if is_sqlite:
        # SQLite: banco num arquivo local.
        # check_same_thread=False é necessário porque o FastAPI
        # usa threads diferentes por request, e o SQLite por padrão
        # só permite acesso da thread que criou a conexão.
        db_path = url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        eng = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=settings.is_development,
        )

        # Ativa foreign keys no SQLite (desabilitado por padrão)
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")   # melhor performance
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return eng

    else:
        # PostgreSQL: servidor de banco dedicado.
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=settings.is_development,
        )


# Engine — a conexão "raiz" com o banco
engine = _build_engine()

# SessionLocal — fábrica de sessões
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Base — classe mãe de todos os models (tabelas)
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
