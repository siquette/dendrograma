"""
ingest_cli.py — Pipeline de Ingestão Sanitizada.
Garante rigor de tipagem e integridade estrutural para a visualização D3.js.
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models.lift import Onda, LiftResultado

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# --- FUNÇÕES DE SANITIZAÇÃO (O SEGREDO PARA O FRONTEND FUNCIONAR) ---
def clean_string(val) -> str:
    if pd.isna(val) or val is None or str(val).strip().lower() == "nan":
        return "Não Informado"
    return str(val).strip()

def clean_float(val) -> float:
    if pd.isna(val) or val is None:
        return 0.0
    return float(val)

def clean_int(val) -> int:
    if pd.isna(val) or val is None:
        return 0
    return int(val)

def process_batch(directory_path: str, onda_codigo: str):
    data_dir = Path(directory_path)
    files = [f for f in data_dir.rglob("*.xlsx") if not f.name.startswith("~$")]
    
    if not files:
        logger.error("Nenhum arquivo .xlsx válido encontrado na pasta.")
        return

    db: Session = SessionLocal()
    
    try:
        # Gestão da Onda
        onda = db.query(Onda).filter(Onda.codigo == onda_codigo).first()
        if not onda:
            onda = Onda(
                codigo=onda_codigo,
                descricao=f"Lote Processado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                data_pesquisa=datetime.now().date(),
                arquivo_origem=files[0].name
            )
            db.add(onda)
            db.commit()
            db.refresh(onda)
            logger.info(f"Onda mapeada: {onda.codigo}")

        total_linhas = 0
        for file_path in files:
            logger.info(f"A sanitizar e ingerir: {file_path.name}")
            try:
                df = pd.read_excel(file_path, sheet_name="BASE_LIFT", engine="openpyxl")
                # Padronização de colunas
                df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
                
                records = []
                for _, row in df.iterrows():
                    record = LiftResultado(
                        onda_id=onda.id,
                        assunto_coluna=clean_string(row.get('assunto_coluna')),
                        pergunta_coluna=clean_string(row.get('pergunta_coluna')),
                        categoria_coluna=clean_string(row.get('categoria_coluna')),
                        assunto_linha=clean_string(row.get('assunto_linha')),
                        pergunta_linha=clean_string(row.get('pergunta_linha')),
                        categoria_linha=clean_string(row.get('categoria_linha')),
                        lift=clean_float(row.get('lift')),
                        base_pergunta_comum=clean_int(row.get('base_pergunta_comum')),
                        base_cat_coluna=clean_int(row.get('base_cat_coluna')),
                        base_cat_linha=clean_int(row.get('base_cat_linha')),
                        base_cat_comum=clean_int(row.get('base_cat_comum')),
                        score_relevancia=clean_float(row.get('score_relevancia')),
                        score_absoluto=clean_float(row.get('score_absoluto')),
                        direcao=clean_string(row.get('direcao')),
                        categoria_direcao=clean_string(row.get('categoria_direcao')),
                        rank_global=clean_int(row.get('rank_global')),
                        percentil_relevancia=clean_float(row.get('percentil_relevancia')),
                        ranking_final=clean_string(row.get('ranking_final'))
                    )
                    records.append(record)
                
                db.bulk_save_objects(records)
                db.commit()
                
                total_linhas += len(records)
                
            except Exception as e:
                logger.error(f"Erro na análise espacial do ficheiro {file_path.name}: {e}")
                db.rollback()
        
        onda.total_registros = total_linhas
        db.commit()
        logger.info(f"Sucesso! {total_linhas} registos limpos inseridos.")

    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=str)
    parser.add_argument("--onda", type=str, required=True)
    args = parser.parse_args()
    process_batch(args.directory, args.onda)