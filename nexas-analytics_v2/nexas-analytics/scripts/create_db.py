"""
create_db.py — Cria as tabelas do SQLite se não existirem.

Roda automaticamente antes do ingest_cli.py, então o usuário não
precisa configurar nada na mão.

Se precisar recriar as tabelas do zero, basta deletar o arquivo do banco
(dados/nexas.db) e rodar esse script de novo.
"""

from backend.database import Base, engine

print("Criando tabelas do banco (se não existirem)...")
Base.metadata.create_all(bind=engine)
print("Pronto!")
