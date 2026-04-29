from sqlalchemy import (
    Column, Integer, String, Text, Numeric,
    Date, DateTime, ForeignKey, func, Index
)
from sqlalchemy.orm import relationship
from backend.database import Base

class Onda(Base):
    """
    Metadados de cada onda de pesquisa.
    """
    __tablename__ = "ondas"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    descricao = Column(Text)
    data_pesquisa = Column(Date)
    data_ingestao = Column(DateTime, server_default=func.now())
    total_registros = Column(Integer)
    arquivo_origem = Column(String(500))

    resultados = relationship("LiftResultado", back_populates="onda", cascade="all, delete-orphan")

class LiftResultado(Base):
    """
    Resultado do Lift Condicional entre dois cruzamentos.
    Otimizado com índices compostos para performance em SQLite com >90k registros.
    """
    __tablename__ = "lift_resultados"

    id = Column(Integer, primary_key=True, index=True)

    # FK para onda - Indexado para carregamento inicial rápido
    onda_id = Column(Integer, ForeignKey("ondas.id", ondelete="CASCADE"), nullable=False, index=True)
    onda = relationship("Onda", back_populates="resultados")

    # --- Cross 1 (coluna) ---
    # Adicionamos índices individuais para buscas genéricas
    assunto_coluna = Column(String(200), nullable=False, index=True)
    pergunta_coluna = Column(Text, nullable=False, index=True)
    categoria_coluna = Column(String(300), nullable=False)

    # --- Cross 2 (linha) ---
    assunto_linha = Column(String(200), nullable=False)
    pergunta_linha = Column(Text, nullable=False)
    categoria_linha = Column(String(300), nullable=False)

    # --- Métricas e Scores ---
    lift = Column(Numeric(12, 6))
    base_pergunta_comum = Column(Integer)
    base_cat_coluna = Column(Integer)
    base_cat_linha = Column(Integer)
    base_cat_comum = Column(Integer)
    score_relevancia = Column(Numeric(12, 6))
    score_absoluto = Column(Numeric(12, 6))

    # --- Classificação ---
    direcao = Column(String(50), index=True) # Indexado para o filtro de Drivers/Anti-drivers
    categoria_direcao = Column(String(100))
    rank_global = Column(Integer)
    percentil_relevancia = Column(Numeric(8, 6))
    ranking_final = Column(String(100))

    # --- ÍNDICES COMPOSTOS (O 'Pulo do Gato' para Performance) ---
    # Criamos um mapa que acelera a query principal do dashboard: Onda + Assunto + Pergunta
    __table_args__ = (
        Index('idx_onda_cruzamento', 'onda_id', 'assunto_coluna', 'pergunta_coluna'),
    )

    def __repr__(self):
        return f"<Lift {self.assunto_coluna} -> {self.categoria_linha}>"