"""
services/tree_builder.py — Transforma a tabela flat em árvore hierárquica.

Esse é o service mais importante do sistema. Ele pega o resultado de uma
query SQL (tabela com linhas e colunas) e monta a árvore aninhada que
o D3 consome para desenhar o dendrograma e o sunburst.

A hierarquia é:
    Nível 0 (root):  ASSUNTO_COLUNA | PERGUNTA_COLUNA
    Nível 1:         CATEGORIA_COLUNA
    Nível 2:         ASSUNTO_LINHA
    Nível 3:         PERGUNTA_LINHA
    Nível 4 (leaf):  CATEGORIA_LINHA  ← com métricas individuais

Cada nó interno (níveis 1-3) recebe métricas AGREGADAS (média dos filhos).
"""

import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.lift import LiftResultado, Onda
from backend.schemas.tree import (
    TreeNode, TreeResponse, TreeContexto,
    LeafMetrics, NodeMetrics,
)

logger = logging.getLogger(__name__)


def build_tree(
    db: Session,
    onda_codigo: str,
    assunto_coluna: str,
    pergunta_coluna: str,
    direcao: str | None = None,
) -> TreeResponse:
    """
    Constrói a árvore hierárquica completa para um cruzamento.

    Args:
        db: Sessão do banco
        onda_codigo: Código da onda (ex: "2025-Q1")
        assunto_coluna: Assunto do cross 1 (ex: "AVALIAÇÃO DA ÁGUA")
        pergunta_coluna: Pergunta do cross 1 (ex: "IQPA")
        direcao: Filtro opcional — "DRIVER", "ANTI-DRIVER" ou None (todos)

    Returns:
        TreeResponse com a árvore completa pronta pro D3
    """

    # --- 1. Buscar a onda ---
    onda = db.query(Onda).filter_by(codigo=onda_codigo).first()
    if not onda:
        raise ValueError(f"Onda '{onda_codigo}' não encontrada.")

    # --- 2. Consultar os dados filtrados ---
    query = db.query(LiftResultado).filter(
        LiftResultado.onda_id == onda.id,
        LiftResultado.assunto_coluna == assunto_coluna,
        LiftResultado.pergunta_coluna == pergunta_coluna,
    )

    if direcao:
        query = query.filter(LiftResultado.direcao == direcao)

    rows = query.all()

    if not rows:
        raise ValueError(
            f"Nenhum resultado para: onda={onda_codigo}, "
            f"assunto={assunto_coluna}, pergunta={pergunta_coluna}"
        )

    logger.info(f"Construindo árvore: {len(rows)} linhas")

    # --- 3. Agrupar em hierarquia ---
    # Monta um dicionário aninhado: cat_coluna → assunto_linha → pergunta_linha → [leaves]
    hierarchy = {}

    for row in rows:
        cat_col = row.categoria_coluna
        ass_lin = row.assunto_linha
        per_lin = row.pergunta_linha
        cat_lin = row.categoria_linha

        if cat_col not in hierarchy:
            hierarchy[cat_col] = {}
        if ass_lin not in hierarchy[cat_col]:
            hierarchy[cat_col][ass_lin] = {}
        if per_lin not in hierarchy[cat_col][ass_lin]:
            hierarchy[cat_col][ass_lin][per_lin] = []

        hierarchy[cat_col][ass_lin][per_lin].append(row)

    # --- 4. Construir a árvore de TreeNodes ---
    root_name = f"{assunto_coluna} | {pergunta_coluna}"
    root_children = []

    for cat_coluna, assuntos in hierarchy.items():
        # Nível 1: CATEGORIA_COLUNA
        nivel1_children = []

        for assunto_linha, perguntas in assuntos.items():
            # Nível 2: ASSUNTO_LINHA
            nivel2_children = []

            for pergunta_linha, leaves in perguntas.items():
                # Nível 3: PERGUNTA_LINHA
                nivel3_children = []

                for row in leaves:
                    # Nível 4: CATEGORIA_LINHA (leaf)
                    leaf_node = TreeNode(
                        name=row.categoria_linha,
                        nivel="categoria_linha",
                        leaf=True,
                        metrics=LeafMetrics(
                            lift=float(row.lift) if row.lift else 0,
                            score_nexas=float(row.score_relevancia) if row.score_relevancia else 0,
                            relevancia=float(row.percentil_relevancia) if row.percentil_relevancia else 0,
                            direcao=row.direcao or "",
                            categoria_direcao=row.categoria_direcao or "",
                            rank_global=row.rank_global,
                            base_comum=row.base_cat_comum,
                        ),
                        value=abs(float(row.score_relevancia)) if row.score_relevancia else 0,
                    )
                    nivel3_children.append(leaf_node)

                # Ordenar leaves por score (maior primeiro)
                nivel3_children.sort(
                    key=lambda n: n.metrics.score_nexas if n.metrics else 0,
                    reverse=True
                )

                # Nó do nível 3 com métricas agregadas
                nivel3_node = TreeNode(
                    name=pergunta_linha,
                    nivel="pergunta_linha",
                    metrics=_aggregate_metrics(nivel3_children),
                    value=_sum_values(nivel3_children),
                    children=nivel3_children,
                )
                nivel2_children.append(nivel3_node)

            # Ordenar por score médio
            nivel2_children.sort(
                key=lambda n: n.metrics.avg_score if isinstance(n.metrics, NodeMetrics) else 0,
                reverse=True
            )

            # Nó do nível 2
            nivel2_node = TreeNode(
                name=assunto_linha,
                nivel="assunto_linha",
                metrics=_aggregate_metrics_from_nodes(nivel2_children),
                value=_sum_values(nivel2_children),
                children=nivel2_children,
            )
            nivel1_children.append(nivel2_node)

        # Ordenar nível 2 por score
        nivel1_children.sort(
            key=lambda n: n.metrics.avg_score if isinstance(n.metrics, NodeMetrics) else 0,
            reverse=True
        )

        # Nó do nível 1
        nivel1_node = TreeNode(
            name=cat_coluna,
            nivel="categoria_coluna",
            metrics=_aggregate_metrics_from_nodes(nivel1_children),
            value=_sum_values(nivel1_children),
            children=nivel1_children,
        )
        root_children.append(nivel1_node)

    # Ordenar nível 1 por score
    root_children.sort(
        key=lambda n: n.metrics.avg_score if isinstance(n.metrics, NodeMetrics) else 0,
        reverse=True
    )

    # Nó root
    root_node = TreeNode(
        name=root_name,
        nivel="root",
        metrics=_aggregate_metrics_from_nodes(root_children),
        value=_sum_values(root_children),
        children=root_children,
    )

    return TreeResponse(
        root=root_name,
        contexto=TreeContexto(
            assunto_coluna=assunto_coluna,
            pergunta_coluna=pergunta_coluna,
            onda=onda_codigo,
            direcao_filtro=direcao,
        ),
        tree=root_node,
    )


def build_ramificacao(
    db: Session,
    onda_codigo: str,
    assunto_coluna: str,
    pergunta_coluna: str,
    categoria_coluna: str,
    direcao: str | None = None,
) -> TreeNode:
    """
    Constrói apenas a subárvore de uma CATEGORIA_COLUNA específica.
    Usado quando o analista clica num arco do sunburst e quer ver
    só aquele ramo no dendrograma.

    Retorna um TreeNode a partir do nível 1 (sem o root).
    """

    onda = db.query(Onda).filter_by(codigo=onda_codigo).first()
    if not onda:
        raise ValueError(f"Onda '{onda_codigo}' não encontrada.")

    query = db.query(LiftResultado).filter(
        LiftResultado.onda_id == onda.id,
        LiftResultado.assunto_coluna == assunto_coluna,
        LiftResultado.pergunta_coluna == pergunta_coluna,
        LiftResultado.categoria_coluna == categoria_coluna,
    )

    if direcao:
        query = query.filter(LiftResultado.direcao == direcao)

    rows = query.all()

    if not rows:
        raise ValueError(
            f"Nenhum resultado para categoria_coluna='{categoria_coluna}'"
        )

    # Montar subárvore (níveis 2-4)
    hierarchy = {}
    for row in rows:
        ass_lin = row.assunto_linha
        per_lin = row.pergunta_linha
        if ass_lin not in hierarchy:
            hierarchy[ass_lin] = {}
        if per_lin not in hierarchy[ass_lin]:
            hierarchy[ass_lin][per_lin] = []
        hierarchy[ass_lin][per_lin].append(row)

    nivel1_children = []

    for assunto_linha, perguntas in hierarchy.items():
        nivel2_children = []

        for pergunta_linha, leaves in perguntas.items():
            nivel3_children = []

            for row in leaves:
                leaf_node = TreeNode(
                    name=row.categoria_linha,
                    nivel="categoria_linha",
                    leaf=True,
                    metrics=LeafMetrics(
                        lift=float(row.lift) if row.lift else 0,
                        score_nexas=float(row.score_relevancia) if row.score_relevancia else 0,
                        relevancia=float(row.percentil_relevancia) if row.percentil_relevancia else 0,
                        direcao=row.direcao or "",
                        categoria_direcao=row.categoria_direcao or "",
                        rank_global=row.rank_global,
                        base_comum=row.base_cat_comum,
                    ),
                    value=abs(float(row.score_relevancia)) if row.score_relevancia else 0,
                )
                nivel3_children.append(leaf_node)

            nivel3_children.sort(
                key=lambda n: n.metrics.score_nexas if n.metrics else 0,
                reverse=True
            )

            nivel3_node = TreeNode(
                name=pergunta_linha,
                nivel="pergunta_linha",
                metrics=_aggregate_metrics(nivel3_children),
                value=_sum_values(nivel3_children),
                children=nivel3_children,
            )
            nivel2_children.append(nivel3_node)

        nivel2_children.sort(
            key=lambda n: n.metrics.avg_score if isinstance(n.metrics, NodeMetrics) else 0,
            reverse=True
        )

        nivel2_node = TreeNode(
            name=assunto_linha,
            nivel="assunto_linha",
            metrics=_aggregate_metrics_from_nodes(nivel2_children),
            value=_sum_values(nivel2_children),
            children=nivel2_children,
        )
        nivel1_children.append(nivel2_node)

    nivel1_children.sort(
        key=lambda n: n.metrics.avg_score if isinstance(n.metrics, NodeMetrics) else 0,
        reverse=True
    )

    return TreeNode(
        name=categoria_coluna,
        nivel="categoria_coluna",
        metrics=_aggregate_metrics_from_nodes(nivel1_children),
        value=_sum_values(nivel1_children),
        children=nivel1_children,
    )


# ============================================
# Funções auxiliares de agregação
# ============================================

def _aggregate_metrics(leaf_nodes: list[TreeNode]) -> NodeMetrics:
    """Calcula métricas agregadas a partir de nós LEAF."""
    scores = []
    relevancias = []

    for node in leaf_nodes:
        if isinstance(node.metrics, LeafMetrics):
            scores.append(node.metrics.score_nexas)
            relevancias.append(node.metrics.relevancia)

    return NodeMetrics(
        avg_score=sum(scores) / len(scores) if scores else 0,
        avg_relevancia=sum(relevancias) / len(relevancias) if relevancias else 0,
        count=len(scores),
    )


def _aggregate_metrics_from_nodes(child_nodes: list[TreeNode]) -> NodeMetrics:
    """Calcula métricas agregadas a partir de nós INTERNOS (que já têm métricas)."""
    scores = []
    relevancias = []
    total_count = 0

    for node in child_nodes:
        if isinstance(node.metrics, NodeMetrics):
            scores.append(node.metrics.avg_score)
            relevancias.append(node.metrics.avg_relevancia)
            total_count += node.metrics.count
        elif isinstance(node.metrics, LeafMetrics):
            scores.append(node.metrics.score_nexas)
            relevancias.append(node.metrics.relevancia)
            total_count += 1

    return NodeMetrics(
        avg_score=sum(scores) / len(scores) if scores else 0,
        avg_relevancia=sum(relevancias) / len(relevancias) if relevancias else 0,
        count=total_count,
    )


def _sum_values(nodes: list[TreeNode]) -> float:
    """Soma os values dos filhos (usado para tamanho do arco no sunburst)."""
    return sum(n.value for n in nodes if n.value)
