"""
filtros.py — Roteador de Metadados e Filtros Analíticos.
Otimizado para SQLite e compatível com a estrutura de dados do frontend.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc, distinct
import re

from backend.database import get_db
from backend.models.lift import Onda, LiftResultado

router = APIRouter(prefix="/api", tags=["dashboard"])

def clean_label(label: Any) -> str:
    """Sanitiza strings do Excel removendo quebras de linha e ruídos de conversão."""
    if label is None or str(label).lower() == "nan":
        return "Não Informado"
    # Remove quebras de linha e espaços duplos que quebram o render do D3.js
    text = re.sub(r'[\r\n\t]+', ' ', str(label)).strip()
    return text if text else "Não Informado"

@router.get("/ondas")
def listar_ondas(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Retorna as ondas disponíveis para inicializar o seletor temporal."""
    ondas = db.query(Onda).order_by(desc(Onda.data_ingestao)).all()
    return [
        {
            "codigo": o.codigo,
            "descricao": o.descricao,
            "data_pesquisa": str(o.data_pesquisa) if o.data_pesquisa else None,
            "total_registros": o.total_registros
        }
        for o in ondas
    ]

@router.get("/filtros")
def obter_filtros(onda: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Retorna a lista completa de Assuntos, Perguntas (agrupadas) e Categorias.
    """
    if not onda:
        onda_obj = db.query(Onda).order_by(desc(Onda.data_ingestao)).first()
    else:
        onda_obj = db.query(Onda).filter(Onda.codigo == onda).first()

    if not onda_obj:
        return {"assuntos": [], "perguntas": {}, "categorias": [], "direcoes": [], "onda_ativa": None}

    # 1. Busca conjunta para mapear Qual Pergunta pertence a Qual Assunto
    perguntas_raw = db.query(
        LiftResultado.assunto_coluna, 
        LiftResultado.pergunta_coluna
    ).filter(LiftResultado.onda_id == onda_obj.id).distinct().all()

    cat_col = db.query(distinct(LiftResultado.categoria_coluna)).filter(LiftResultado.onda_id == onda_obj.id).all()
    cat_lin = db.query(distinct(LiftResultado.categoria_linha)).filter(LiftResultado.onda_id == onda_obj.id).all()
    direcoes_raw = db.query(distinct(LiftResultado.direcao)).filter(LiftResultado.onda_id == onda_obj.id).all()

    # 2. Processamento e Construção do Dicionário
    perguntas_dict = {}
    for assunto, pergunta in perguntas_raw:
        a_limpo = clean_label(assunto)
        p_limpo = clean_label(pergunta)
        
        if a_limpo not in perguntas_dict:
            perguntas_dict[a_limpo] = []
        
        if p_limpo not in perguntas_dict[a_limpo]:
            perguntas_dict[a_limpo].append(p_limpo)

    # Assuntos são extraídos diretamente das chaves do dicionário
    assuntos = sorted(list(perguntas_dict.keys()))
    
    # Ordenar as perguntas em ordem alfabética dentro de cada assunto
    for a in perguntas_dict:
        perguntas_dict[a].sort()

    # 3. Merge de categorias
    set_categorias = set([clean_label(c[0]) for c in cat_col if c[0]])
    set_categorias.update([clean_label(c[0]) for c in cat_lin if c[0]])
    
    categorias = sorted([c for c in set_categorias if c != "Não Informado"])
    direcoes = sorted([clean_label(d[0]) for d in direcoes_raw if d[0]])

    return {
        "onda_ativa": onda_obj.codigo,
        "assuntos": assuntos,
        "perguntas": perguntas_dict,  # <-- Agora enviamos o mapeamento correto!
        "categorias": categorias,
        "direcoes": direcoes
    }