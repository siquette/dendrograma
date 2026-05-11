"""
routers/filtros.py — Endpoints que populam os dropdowns do frontend.

São os primeiros endpoints que o frontend chama quando carrega.
Devolvem as opções disponíveis para o analista selecionar.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct

from backend.database import get_db
from backend.models.lift import LiftResultado, Onda
from backend.schemas.tree import (
    OndaResponse, FiltrosResponse,
    FiltrosPerguntasResponse, FiltrosCategoriasResponse,
)

router = APIRouter(prefix="/api", tags=["filtros"])


@router.get("/ondas", response_model=list[OndaResponse])
def listar_ondas(db: Session = Depends(get_db)):
    """Lista todas as ondas disponíveis, da mais recente para a mais antiga."""
    ondas = db.query(Onda).order_by(Onda.data_ingestao.desc()).all()
    return [
        OndaResponse(
            codigo=o.codigo,
            descricao=o.descricao,
            data_pesquisa=str(o.data_pesquisa) if o.data_pesquisa else None,
            total_registros=o.total_registros,
        )
        for o in ondas
    ]
@router.get("/assuntos")
def listar_assuntos(
    onda: str = Query(..., description="Código da onda"),
    db: Session = Depends(get_db),
):
    """Lista assuntos disponíveis para uma onda."""
    onda_obj = db.query(Onda).filter_by(codigo=onda).first()
    if not onda_obj:
        return []

    assuntos = [
        row[0] for row in
        db.query(distinct(LiftResultado.assunto_coluna))
        .filter(LiftResultado.onda_id == onda_obj.id)
        .order_by(LiftResultado.assunto_coluna)
        .all()
    ]
    
    return assuntos


@router.get("/perguntas")
def listar_perguntas_simples(
    onda: str = Query(...),
    assunto: str = Query(...),
    db: Session = Depends(get_db),
):
    """Perguntas disponíveis para um assunto específico."""
    onda_obj = db.query(Onda).filter_by(codigo=onda).first()
    if not onda_obj:
        return []

    perguntas = [
        row[0] for row in
        db.query(distinct(LiftResultado.pergunta_coluna))
        .filter(
            LiftResultado.onda_id == onda_obj.id,
            LiftResultado.assunto_coluna == assunto,
        )
        .order_by(LiftResultado.pergunta_coluna)
        .all()
    ]

    return perguntas

@router.get("/filtros", response_model=FiltrosResponse)
def listar_filtros(
    onda: str = Query(..., description="Código da onda"),
    db: Session = Depends(get_db),
):
    """
    Lista todos os assuntos, perguntas e categorias disponíveis.
    Usado para popular os dropdowns em cascata:
    Assunto → Pergunta → Categoria
    """
    onda_obj = db.query(Onda).filter_by(codigo=onda).first()
    if not onda_obj:
        return FiltrosResponse(assuntos=[], perguntas={}, categorias={})

    base = db.query(LiftResultado).filter(LiftResultado.onda_id == onda_obj.id)

    # Assuntos distintos
    assuntos = [
        row[0] for row in
        base.with_entities(distinct(LiftResultado.assunto_coluna))
        .order_by(LiftResultado.assunto_coluna)
        .all()
    ]

    # Perguntas agrupadas por assunto
    perguntas_raw = (
        base.with_entities(
            LiftResultado.assunto_coluna,
            LiftResultado.pergunta_coluna,
        )
        .group_by(LiftResultado.assunto_coluna, LiftResultado.pergunta_coluna)
        .order_by(LiftResultado.assunto_coluna, LiftResultado.pergunta_coluna)
        .all()
    )
    perguntas = {}
    for assunto, pergunta in perguntas_raw:
        if assunto not in perguntas:
            perguntas[assunto] = []
        perguntas[assunto].append(pergunta)

    # Categorias agrupadas por pergunta
    categorias_raw = (
        base.with_entities(
            LiftResultado.pergunta_coluna,
            LiftResultado.categoria_coluna,
        )
        .group_by(LiftResultado.pergunta_coluna, LiftResultado.categoria_coluna)
        .order_by(LiftResultado.pergunta_coluna, LiftResultado.categoria_coluna)
        .all()
    )
    categorias = {}
    for pergunta, categoria in categorias_raw:
        if pergunta not in categorias:
            categorias[pergunta] = []
        categorias[pergunta].append(categoria)

    return FiltrosResponse(
        assuntos=assuntos,
        perguntas=perguntas,
        categorias=categorias,
    )


@router.get("/filtros/perguntas", response_model=FiltrosPerguntasResponse)
def listar_perguntas(
    onda: str = Query(...),
    assunto: str = Query(...),
    db: Session = Depends(get_db),
):
    """Perguntas disponíveis para um assunto específico."""
    onda_obj = db.query(Onda).filter_by(codigo=onda).first()
    if not onda_obj:
        return FiltrosPerguntasResponse(assunto=assunto, perguntas=[])

    perguntas = [
        row[0] for row in
        db.query(distinct(LiftResultado.pergunta_coluna))
        .filter(
            LiftResultado.onda_id == onda_obj.id,
            LiftResultado.assunto_coluna == assunto,
        )
        .order_by(LiftResultado.pergunta_coluna)
        .all()
    ]

    return FiltrosPerguntasResponse(assunto=assunto, perguntas=perguntas)


@router.get("/filtros/categorias", response_model=FiltrosCategoriasResponse)
def listar_categorias(
    onda: str = Query(...),
    assunto: str = Query(...),
    pergunta: str = Query(...),
    db: Session = Depends(get_db),
):
    """Categorias disponíveis para uma pergunta específica."""
    onda_obj = db.query(Onda).filter_by(codigo=onda).first()
    if not onda_obj:
        return FiltrosCategoriasResponse(pergunta=pergunta, categorias=[])

    categorias = [
        row[0] for row in
        db.query(distinct(LiftResultado.categoria_coluna))
        .filter(
            LiftResultado.onda_id == onda_obj.id,
            LiftResultado.assunto_coluna == assunto,
            LiftResultado.pergunta_coluna == pergunta,
        )
        .order_by(LiftResultado.categoria_coluna)
        .all()
    ]

    return FiltrosCategoriasResponse(pergunta=pergunta, categorias=categorias)