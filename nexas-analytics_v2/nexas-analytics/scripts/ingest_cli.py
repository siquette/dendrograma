"""
scripts/ingest_cli.py — Script de linha de comando para ingestão de XLSX.

Uso:
    python -m scripts.ingest_cli dados\WORKBOOK_ANALISE_VERSAO_INICIAL_2.xlsx --onda 2025-Q1

Roda INDEPENDENTE do FastAPI — não precisa do servidor de pé.
Conecta direto no banco e insere os dados.
Cria as tabelas automaticamente se não existirem.
"""

import argparse
import sys
import logging
from pathlib import Path

# Adiciona o diretório raiz ao path pra importar o backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import Base, engine, SessionLocal
from backend.services.ingestor import ingest_xlsx, IngestorError


def main():
    parser = argparse.ArgumentParser(
        description="NEXAS Analytics — Ingestão de XLSX"
    )
    parser.add_argument(
        "arquivo",
        type=str,
        help="Caminho do arquivo XLSX",
    )
    parser.add_argument(
        "--onda",
        required=True,
        help="Código da onda (ex: 2025-Q1)",
    )
    parser.add_argument(
        "--descricao",
        default=None,
        help="Descrição da onda (opcional)",
    )
    parser.add_argument(
        "--sheet",
        default="BASE_LIFT",
        help="Nome da sheet a ler (default: BASE_LIFT)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logger = logging.getLogger(__name__)

    filepath = Path(args.arquivo)
    if not filepath.exists():
        logger.error(f"Arquivo não encontrado: {filepath}")
        sys.exit(1)

    # Cria as tabelas se não existirem
    logger.info("Verificando banco de dados...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        logger.info(f"Iniciando ingestão: {filepath.name} → onda '{args.onda}'")

        result = ingest_xlsx(
            db=db,
            filepath=filepath,
            onda_codigo=args.onda,
            onda_descricao=args.descricao,
            sheet_name=args.sheet,
        )

        logger.info(f"Ingestão concluída com sucesso!")
        logger.info(f"  Onda: {result.onda_codigo}")
        logger.info(f"  Registros inseridos: {result.total_inseridos}")

        if result.warnings:
            for w in result.warnings:
                logger.warning(f"  {w}")

    except IngestorError as e:
        logger.error(f"Erro na ingestão: {e}")
        db.rollback()
        sys.exit(1)

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
