"""
services/aggregator.py — Calcula métricas resumidas para o painel do dashboard.

Enquanto o tree_builder monta a hierarquia visual, o aggregator fornece
os números que aparecem no painel inferior:
- Total de drivers / anti-drivers
- Top score
- Distribuição por categoria de direção

São queries de agregação diretas no banco — rápidas e simples.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.lift import LiftResultado, Onda
from backend.schemas.tree import MetricasResumo


def get_metricas_resumo(
    db: Session,
    onda_codigo: str,
    assunto_coluna: str,
    pergunta_coluna: str,
    direcao: str | None = None,
) -> MetricasResumo:
    """
    Calcula métricas agregadas para um cruzamento específico.

    Usado no painel de métricas do rodapé do dashboard.
    """

    onda = db.query(Onda).filter_by(codigo=onda_codigo).first()
    if not onda:
        raise ValueError(f"Onda '{onda_codigo}' não encontrada.")

    # Query base
    base_query = db.query(LiftResultado).filter(
        LiftResultado.onda_id == onda.id,
        LiftResultado.assunto_coluna == assunto_coluna,
        LiftResultado.pergunta_coluna == pergunta_coluna,
    )

    if direcao:
        base_query = base_query.filter(LiftResultado.direcao == direcao)

    # Total de cruzamentos
    total = base_query.count()

    # Contagem por direção
    direcao_counts = (
        base_query
        .with_entities(LiftResultado.direcao, func.count())
        .group_by(LiftResultado.direcao)
        .all()
    )
    direcao_map = {d: c for d, c in direcao_counts}

    # Contagem por categoria de direção
    cat_direcao_counts = (
        base_query
        .with_entities(LiftResultado.categoria_direcao, func.count())
        .group_by(LiftResultado.categoria_direcao)
        .all()
    )
    distribuicao = {cat: count for cat, count in cat_direcao_counts if cat}

    # Top score
    top_row = (
        base_query
        .order_by(LiftResultado.score_relevancia.desc())
        .first()
    )

    return MetricasResumo(
        total_cruzamentos=total,
        total_drivers=direcao_map.get("DRIVER", 0),
        total_anti_drivers=direcao_map.get("ANTI-DRIVER", 0),
        total_baixa_relevancia=direcao_map.get("BAIXA RELEVÂNCIA", 0),
        top_score=float(top_row.score_relevancia) if top_row and top_row.score_relevancia else 0,
        top_categoria=top_row.categoria_linha if top_row else "",
        distribuicao_direcao=distribuicao,
    )
