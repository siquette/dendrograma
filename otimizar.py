from backend.database import engine
from sqlalchemy import text

print("Iniciando criação de índices no SQLite...")
with engine.connect() as conn:
    # Cria o índice composto para acelerar filtros de Assunto e Pergunta
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_onda_cruzamento 
        ON lift_resultados (onda_id, assunto_coluna, pergunta_coluna)
    """))
    
    # Cria índice para a coluna de Direção (Drivers/Anti-drivers)
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_direcao ON lift_resultados (direcao)"))
    
    conn.commit()
    print("Otimização concluída com sucesso! Agora as buscas serão instantâneas.")
    