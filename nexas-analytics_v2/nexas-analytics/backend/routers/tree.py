"""
routers/tree.py — Endpoints das visualizações (dendrograma e sunburst).

São endpoints finos: recebem os parâmetros, chamam o service,
devolvem o resultado. A lógica pesada está no tree_builder.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.tree import TreeResponse, TreeNode, MetricasResumo
from backend.services.tree_builder import build_tree, build_ramificacao
from backend.services.aggregator import get_metricas_resumo

router = APIRouter(prefix="/api", tags=["visualizações"])

@router.get("/tree", response_model=TreeResponse)

def get_tree(
    onda: str = Query(..., description="Código da onda"),
    assunto: str = Query(..., description="ASSUNTO_COLUNA"),
    pergunta: str = Query(..., description="PERGUNTA_COLUNA"),
    direcao: str | None = Query(None, description="DRIVER, ANTI-DRIVER ou vazio para todos"),
    agregacao: str = Query("weighted_mean", description="Método: weighted_mean, mean, median, max"),  # ← NOVO
    db: Session = Depends(get_db),
):
    """
    Retorna a árvore hierárquica completa para um cruzamento.
    """
    try:
        return build_tree(db, onda, assunto, pergunta, direcao, agregacao)  # ← Passar agregacao
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/ramificacao", response_model=TreeNode)
def get_ramificacao(
    onda: str = Query(...),
    assunto: str = Query(..., description="ASSUNTO_COLUNA"),
    pergunta: str = Query(..., description="PERGUNTA_COLUNA"),
    categoria: str = Query(..., description="CATEGORIA_COLUNA selecionada"),
    direcao: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Retorna a subárvore de uma CATEGORIA_COLUNA específica.
    Usado quando o analista clica num arco do sunburst —
    o dendrograma ao lado renderiza só esse ramo.
    """
    try:
        return build_ramificacao(db, onda, assunto, pergunta, categoria, direcao)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/metricas", response_model=MetricasResumo)
def get_metricas(
    onda: str = Query(...),
    assunto: str = Query(...),
    pergunta: str = Query(...),
    direcao: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    Retorna métricas resumidas para o painel inferior do dashboard.
    Total de drivers, anti-drivers, top score, distribuição.
    """
    try:
        return get_metricas_resumo(db, onda, assunto, pergunta, direcao)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
