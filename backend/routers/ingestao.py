"""
routers/ingestao.py — Endpoint de upload de XLSX.

Permite ingerir dados pela interface web (futuro)
ou via chamada HTTP direta (Postman, curl, etc.).
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import tempfile
import shutil
from pathlib import Path

from backend.database import get_db
from backend.services.ingestor import ingest_xlsx, IngestorError

router = APIRouter(prefix="/api/ingestao", tags=["ingestão"])


@router.post("/upload")
def upload_xlsx(
    arquivo: UploadFile = File(..., description="Arquivo XLSX com a BASE_LIFT"),
    onda: str = Form(..., description="Código da onda (ex: 2025-Q1)"),
    descricao: str = Form(None, description="Descrição da onda"),
    db: Session = Depends(get_db),
):
    """
    Recebe um XLSX, valida e insere no banco.

    O arquivo é salvo temporariamente no servidor,
    processado pelo ingestor, e depois deletado.
    """

    # Verificar extensão
    if not arquivo.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Envie um arquivo .xlsx"
        )

    # Salvar em arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(arquivo.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        result = ingest_xlsx(
            db=db,
            filepath=tmp_path,
            onda_codigo=onda,
            onda_descricao=descricao,
        )

        return {
            "status": "success",
            "onda": result.onda_codigo,
            "registros_inseridos": result.total_inseridos,
            "warnings": result.warnings,
        }

    except IngestorError as e:
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        # Limpar arquivo temporário
        tmp_path.unlink(missing_ok=True)
