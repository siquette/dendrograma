"""
models/lift.py — Modelos SQLAlchemy das tabelas do banco.

Cada classe aqui é um espelho de uma tabela no PostgreSQL.
O SQLAlchemy traduz operações Python em SQL automaticamente:

    db.query(LiftResultado).filter_by(assunto_coluna="AVALIAÇÃO DA ÁGUA")
    →  SELECT * FROM lift_resultados WHERE assunto_coluna = 'AVALIAÇÃO DA ÁGUA'

Os nomes das colunas seguem EXATAMENTE os nomes do XLSX original,
convertidos para snake_case. Isso evita mapeamentos confusos.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Numeric,
    Date, DateTime, ForeignKey, func
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Onda(Base):
    """
    Metadados de cada onda de pesquisa.
    Cada XLSX ingerido vira um registro aqui.
    Permite filtrar resultados por período e comparar ondas.
    """
    __tablename__ = "ondas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)      # "2025-Q1"
    descricao = Column(Text)
    data_pesquisa = Column(Date)
    data_ingestao = Column(DateTime, server_default=func.now())
    total_registros = Column(Integer)
    arquivo_origem = Column(String(500))

    # Relacionamento: uma onda tem muitos resultados
    resultados = relationship("LiftResultado", back_populates="onda", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Onda {self.codigo} ({self.total_registros} registros)>"


class LiftResultado(Base):
    """
    Resultado do Lift Condicional entre dois cruzamentos.

    Cada linha representa: dado que o respondente está na CATEGORIA_COLUNA
    de uma PERGUNTA_COLUNA (cross 1), qual a força de associação com
    a CATEGORIA_LINHA de uma PERGUNTA_LINHA (cross 2)?

    Essa tabela é o coração do sistema — é dela que saem o dendrograma,
    o sunburst e todas as métricas.
    """
    __tablename__ = "lift_resultados"

    id = Column(Integer, primary_key=True, index=True)

    # FK para onda
    onda_id = Column(Integer, ForeignKey("ondas.id", ondelete="CASCADE"), nullable=False)
    onda = relationship("Onda", back_populates="resultados")

    # --- Cross 1 (coluna) — o indicador/pergunta-base ---
    assunto_coluna = Column(String(200), nullable=False)
    pergunta_coluna = Column(Text, nullable=False)
    categoria_coluna = Column(String(300), nullable=False)

    # --- Cross 2 (linha) — a variável associada ---
    assunto_linha = Column(String(200), nullable=False)
    pergunta_linha = Column(Text, nullable=False)
    categoria_linha = Column(String(300), nullable=False)

    # --- Métricas de associação ---
    lift = Column(Numeric(12, 6))                       # Lift condicional
    base_pergunta_comum = Column(Integer)               # Respondentes ambas perguntas
    base_cat_coluna = Column(Integer)                   # Respondentes cat coluna
    base_cat_linha = Column(Integer)                    # Respondentes cat linha
    base_cat_comum = Column(Integer)                    # Respondentes ambas categorias

    # --- Scores calculados ---
    score_relevancia = Column(Numeric(12, 6))           # Score Nexas
    score_absoluto = Column(Numeric(12, 6))

    # --- Classificação ---
    direcao = Column(String(50))                        # DRIVER, ANTI-DRIVER, BAIXA RELEVÂNCIA
    categoria_direcao = Column(String(100))             # DRIVER FORTE, RELEVANTE, MODERADO, etc.
    rank_global = Column(Integer)
    percentil_relevancia = Column(Numeric(8, 6))        # 0 a 1
    ranking_final = Column(String(100))                 # TOP ABSOLUTO, CLASSIFICAÇÃO MEDIANA, etc.

    def __repr__(self):
        return (
            f"<Lift {self.assunto_coluna}|{self.categoria_coluna} "
            f"→ {self.categoria_linha} = {self.lift}>"
        )
