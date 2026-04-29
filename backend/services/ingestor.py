"""
services/ingestor.py — Lê o XLSX, valida e insere no PostgreSQL.

Esse é o ponto de entrada dos dados no sistema.
Quando chega um XLSX novo da pesquisa, esse service:
1. Lê o arquivo com pandas
2. Valida se a estrutura está correta (colunas, tipos)
3. Cria um registro na tabela ondas
4. Insere os dados na tabela lift_resultados

O XLSX chega pronto (lift já calculado). Esse service
NÃO faz cálculos — só valida e persiste.
"""

import logging
from pathlib import Path
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from backend.models.lift import Onda, LiftResultado

logger = logging.getLogger(__name__)


# Mapeamento: nome da coluna no XLSX → nome da coluna no banco
# Os nomes do XLSX têm espaços, acentos e nomes longos.
# O banco usa snake_case limpo.
COLUMN_MAP = {
    "ASSUNTO_COLUNA": "assunto_coluna",
    "PERGUNTA_COLUNA": "pergunta_coluna",
    "CATEGORIA_COLUNA": "categoria_coluna",
    "ASSUNTO_LINHA": "assunto_linha",
    "PERGUNTA_LINHA": "pergunta_linha",
    "CATEGORIA_LINHA": "categoria_linha",
    "LIFT (intensidade relativa)": "lift",
    "BASE RESPONDENTE DA PERGUNTA EM COMUM": "base_pergunta_comum",
    "BASE RESPONDENTE CATEGORIA DA COLUNA": "base_cat_coluna",
    "BASE RESPONDENTE CATEGORIA DA LINHA": "base_cat_linha",
    "BASE RESPONDENTE DA CATEGORIA EM COMUM": "base_cat_comum",
    "SCORE DE RELEVÂNCIA": "score_relevancia",
    "SCORE ABSOLUTO": "score_absoluto",
    "DIREÇÃO": "direcao",
    "CATEGORIA DA DIREÇÃO": "categoria_direcao",
    "RANK": "rank_global",
    "RANK - PERCENTIL DE RELEVÂNCIA": "percentil_relevancia",
    "RANKING FINAL DE DRIVERS": "ranking_final",
}

# Colunas obrigatórias no XLSX (se faltar alguma, rejeita)
REQUIRED_COLUMNS = set(COLUMN_MAP.keys())


class IngestorError(Exception):
    """Erro durante a ingestão de dados."""
    pass


class IngestorResult:
    """Resultado da ingestão — usado pra reportar sucesso ou problemas."""
    def __init__(self, onda_codigo: str):
        self.onda_codigo = onda_codigo
        self.total_inseridos = 0
        self.warnings: list[str] = []
        self.success = False

    def __repr__(self):
        status = "OK" if self.success else "FALHOU"
        return f"<Ingestão {self.onda_codigo}: {status} | {self.total_inseridos} registros>"


def validate_xlsx(df: pd.DataFrame) -> list[str]:
    """
    Valida se o DataFrame tem a estrutura esperada.
    Retorna lista de warnings (vazia se tudo ok).
    Lança IngestorError se houver problema crítico.
    """
    warnings = []

    # Checar colunas obrigatórias
    colunas_presentes = set(df.columns)
    faltando = REQUIRED_COLUMNS - colunas_presentes
    if faltando:
        raise IngestorError(
            f"Colunas obrigatórias ausentes no XLSX: {faltando}"
        )

    # Checar colunas extras (não é erro, mas vale avisar)
    extras = colunas_presentes - REQUIRED_COLUMNS
    if extras:
        warnings.append(f"Colunas extras ignoradas: {extras}")

    # Checar se não está vazio
    if len(df) == 0:
        raise IngestorError("O XLSX não contém dados (0 linhas).")

    # Checar se LIFT é numérico
    if not pd.api.types.is_numeric_dtype(df["LIFT (intensidade relativa)"]):
        raise IngestorError("Coluna LIFT não é numérica.")

    # Checar valores nulos nas colunas de chave
    key_cols = [
        "ASSUNTO_COLUNA", "PERGUNTA_COLUNA", "CATEGORIA_COLUNA",
        "ASSUNTO_LINHA", "PERGUNTA_LINHA", "CATEGORIA_LINHA",
    ]
    for col in key_cols:
        nulos = df[col].isna().sum()
        if nulos > 0:
            warnings.append(f"Coluna {col} tem {nulos} valores nulos.")

    return warnings


def ingest_xlsx(
    db: Session,
    filepath: str | Path,
    onda_codigo: str,
    onda_descricao: str | None = None,
    data_pesquisa: date | None = None,
    sheet_name: str = "BASE_LIFT",
) -> IngestorResult:
    """
    Ingere um arquivo XLSX no banco de dados.

    Args:
        db: Sessão do SQLAlchemy
        filepath: Caminho do arquivo XLSX
        onda_codigo: Identificador da onda (ex: "2025-Q1")
        onda_descricao: Descrição opcional
        data_pesquisa: Data de referência da coleta
        sheet_name: Nome da sheet a ler (default: "BASE_LIFT")

    Returns:
        IngestorResult com detalhes da operação
    """
    result = IngestorResult(onda_codigo)
    filepath = Path(filepath)

    # --- 1. Verificar se o arquivo existe ---
    if not filepath.exists():
        raise IngestorError(f"Arquivo não encontrado: {filepath}")

    if not filepath.suffix.lower() in (".xlsx", ".xls"):
        raise IngestorError(f"Formato não suportado: {filepath.suffix}")

    logger.info(f"Lendo arquivo: {filepath}")

    # --- 2. Ler o XLSX ---
    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
    except Exception as e:
        raise IngestorError(f"Erro ao ler o XLSX: {e}")

    logger.info(f"Arquivo lido: {len(df)} linhas, {len(df.columns)} colunas")

    # --- 3. Validar estrutura ---
    result.warnings = validate_xlsx(df)
    for w in result.warnings:
        logger.warning(w)

    # --- 4. Verificar se a onda já existe ---
    onda_existente = db.query(Onda).filter_by(codigo=onda_codigo).first()
    if onda_existente:
        raise IngestorError(
            f"Onda '{onda_codigo}' já existe no banco ({onda_existente.total_registros} registros). "
            f"Delete a onda existente antes de reingerir."
        )

    # --- 5. Criar registro da onda ---
    onda = Onda(
        codigo=onda_codigo,
        descricao=onda_descricao,
        data_pesquisa=data_pesquisa,
        total_registros=len(df),
        arquivo_origem=filepath.name,
    )
    db.add(onda)
    db.flush()  # Gera o onda.id sem commitar

    logger.info(f"Onda criada: {onda}")

    # --- 6. Preparar e inserir dados ---
    # Renomeia colunas do XLSX para o padrão do banco
    df_renamed = df[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)

    # Adiciona a FK da onda
    df_renamed["onda_id"] = onda.id

    # Limpa NaNs problemáticos para inteiros
    int_cols = ["base_pergunta_comum", "base_cat_coluna", "base_cat_linha",
                "base_cat_comum", "rank_global"]
    for col in int_cols:
        if col in df_renamed.columns:
            df_renamed[col] = df_renamed[col].where(df_renamed[col].notna(), None)

    # Inserção em batch (muito mais rápido que um INSERT por linha)
    records = df_renamed.to_dict(orient="records")

    # Inserir em chunks de 5000 (evita estouro de memória em bases grandes)
    chunk_size = 5000
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        db.bulk_insert_mappings(LiftResultado, chunk)
        logger.info(f"  Inseridos {min(i + chunk_size, len(records))}/{len(records)}")

    # --- 7. Commit ---
    db.commit()

    result.total_inseridos = len(records)
    result.success = True
    logger.info(f"Ingestão concluída: {result}")

    return result
