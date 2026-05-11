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

MODIFICAÇÕES v2.0:
- Adicionado cálculo de composição Driver/Anti-driver
- Adicionado min_score, max_score, median_score, std_dev
- Composição retorna count, percentage, avg, max/min para cada tipo
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
    agregacao: str | None = None,  # ← PARÂMETRO ADICIONADO AQUI
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

def _calculate_composition(leaf_nodes: list[TreeNode]) -> dict | None:
    """
    Calcula composição de drivers vs anti-drivers a partir de leafs.
    
    Retorna estatísticas separadas para cada tipo de direção:
    - Drivers: count, percentage, avg, max
    - Anti-drivers: count, percentage, avg, min
    
    Returns:
        {
            'drivers': {'count': int, 'percentage': float, 'avg': float, 'max': float},
            'anti_drivers': {'count': int, 'percentage': float, 'avg': float, 'min': float}
        }
        ou None se não houver leafs com direção definida
    """
    drivers = []
    anti_drivers = []
    
    for node in leaf_nodes:
        if isinstance(node.metrics, LeafMetrics):
            if node.metrics.direcao == 'DRIVER':
                drivers.append(node.metrics.score_nexas)
            elif node.metrics.direcao == 'ANTI-DRIVER':
                anti_drivers.append(node.metrics.score_nexas)
    
    total = len(drivers) + len(anti_drivers)
    if total == 0:
        return None
    
    result = {}
    
    if drivers:
        result['drivers'] = {
            'count': len(drivers),
            'percentage': round((len(drivers) / total) * 100, 1),
            'avg': round(sum(drivers) / len(drivers), 1),
            'max': round(max(drivers), 1)
        }
    
    if anti_drivers:
        result['anti_drivers'] = {
            'count': len(anti_drivers),
            'percentage': round((len(anti_drivers) / total) * 100, 1),
            'avg': round(sum(anti_drivers) / len(anti_drivers), 1),
            'min': round(min(anti_drivers), 1)
        }
    
    return result if result else None


def _aggregate_metrics(leaf_nodes: list[TreeNode]) -> NodeMetrics:
    """
    Calcula métricas agregadas a partir de nós LEAF.
    
    MODIFICADO v2.0: Agora inclui composição Driver/Anti-driver
    """
    scores = []
    relevancias = []

    for node in leaf_nodes:
        if isinstance(node.metrics, LeafMetrics):
            scores.append(node.metrics.score_nexas)
            relevancias.append(node.metrics.relevancia)

    # Estatísticas básicas
    avg_score = sum(scores) / len(scores) if scores else 0
    min_score = min(scores) if scores else 0
    max_score = max(scores) if scores else 0
    
    # Mediana
    sorted_scores = sorted(scores) if scores else [0]
    n = len(sorted_scores)
    median_score = (sorted_scores[n//2] if n % 2 else (sorted_scores[n//2-1] + sorted_scores[n//2])/2)
    
    # Desvio padrão
    if len(scores) > 1:
        variance = sum((x - avg_score) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5
    else:
        std_dev = 0
    
    # NOVO: Composição Driver/Anti-driver
    composition = _calculate_composition(leaf_nodes)

    return NodeMetrics(
        avg_score=avg_score,
        min_score=min_score,
        max_score=max_score,
        median_score=median_score,
        std_dev=std_dev,
        avg_relevancia=sum(relevancias) / len(relevancias) if relevancias else 0,
        count=len(scores),
        composition=composition,
    )


def _aggregate_metrics_from_nodes(child_nodes: list[TreeNode]) -> NodeMetrics:
    """
    Calcula métricas agregadas a partir de nós INTERNOS (que já têm métricas).
    
    MODIFICADO v2.0: Propaga composição dos filhos para o pai
    """
    scores = []
    relevancias = []
    total_count = 0
    all_min_scores = []
    all_max_scores = []
    
    # Coletar todos os leafs descendentes para composição
    all_leaf_nodes = []
    
    def collect_leaves(node: TreeNode):
        if node.leaf:
            all_leaf_nodes.append(node)
        elif node.children:
            for child in node.children:
                collect_leaves(child)
    
    for node in child_nodes:
        collect_leaves(node)
        
        if isinstance(node.metrics, NodeMetrics):
            scores.append(node.metrics.avg_score)
            relevancias.append(node.metrics.avg_relevancia)
            total_count += node.metrics.count
            if hasattr(node.metrics, 'min_score') and node.metrics.min_score is not None:
                all_min_scores.append(node.metrics.min_score)
            if hasattr(node.metrics, 'max_score') and node.metrics.max_score is not None:
                all_max_scores.append(node.metrics.max_score)
        elif isinstance(node.metrics, LeafMetrics):
            scores.append(node.metrics.score_nexas)
            relevancias.append(node.metrics.relevancia)
            total_count += 1
            all_min_scores.append(node.metrics.score_nexas)
            all_max_scores.append(node.metrics.score_nexas)

    avg_score = sum(scores) / len(scores) if scores else 0
    min_score = min(all_min_scores) if all_min_scores else 0
    max_score = max(all_max_scores) if all_max_scores else 0
    
    # Mediana dos scores médios
    sorted_scores = sorted(scores) if scores else [0]
    n = len(sorted_scores)
    median_score = (sorted_scores[n//2] if n % 2 else (sorted_scores[n//2-1] + sorted_scores[n//2])/2)
    
    # Desvio padrão dos scores médios
    if len(scores) > 1:
        variance = sum((x - avg_score) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5
    else:
        std_dev = 0
    
    # Calcular composição a partir de TODOS os leafs descendentes
    composition = _calculate_composition(all_leaf_nodes) if all_leaf_nodes else None

    return NodeMetrics(
        avg_score=avg_score,
        min_score=min_score,
        max_score=max_score,
        median_score=median_score,
        std_dev=std_dev,
        avg_relevancia=sum(relevancias) / len(relevancias) if relevancias else 0,
        count=total_count,
        composition=composition,
    )


def _sum_values(nodes: list[TreeNode]) -> float:
    """Soma os values dos filhos (usado para tamanho do arco no sunburst)."""
    return sum(n.value for n in nodes if n.value)
