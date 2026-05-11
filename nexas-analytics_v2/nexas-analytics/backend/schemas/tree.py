"""
schemas/tree.py — Define o formato exato do JSON que a API retorna.

Isso é o CONTRATO entre backend e frontend.
Se o backend retornar algo diferente, o Pydantic dá erro.
Se o frontend espera algo diferente, a gente muda aqui.

Por que separar schemas de models?
- Model (lift.py): como o dado vive no banco (tabela flat, linhas e colunas)
- Schema (tree.py): como o dado sai na API (JSON hierárquico, árvore aninhada)
São formatos completamente diferentes.
"""

from __future__ import annotations

from pydantic import BaseModel


# ============================================
# Schemas do dendrograma / sunburst
# ============================================

class LeafMetrics(BaseModel):
    """Métricas de um nó folha (CATEGORIA_LINHA) — o nível mais profundo."""
    lift: float
    score_nexas: float
    relevancia: float
    direcao: str
    categoria_direcao: str
    rank_global: int | None = None
    base_comum: int | None = None


class NodeMetrics(BaseModel):
    avg_score: float
    min_score: float = 0           # ADICIONAR
    max_score: float = 0           # ADICIONAR
    median_score: float = 0        # ADICIONAR
    std_dev: float = 0             # ADICIONAR
    avg_relevancia: float
    count: int
    composition: dict | None = None  # NOVO!

class TreeNode(BaseModel):
    """
    Nó da árvore hierárquica — usado tanto no dendrograma quanto no sunburst.

    A estrutura é recursiva: cada nó pode ter filhos que também são TreeNodes.

    Níveis:
        0 (root)  → name = ASSUNTO_COLUNA | PERGUNTA_COLUNA
        1         → name = CATEGORIA_COLUNA        (nivel = "categoria_coluna")
        2         → name = ASSUNTO_LINHA            (nivel = "assunto_linha")
        3         → name = PERGUNTA_LINHA           (nivel = "pergunta_linha")
        4 (leaf)  → name = CATEGORIA_LINHA          (nivel = "categoria_linha")
    """
    name: str
    nivel: str
    leaf: bool = False

    # Um nó tem OU métricas de leaf OU métricas agregadas, nunca ambos
    metrics: LeafMetrics | NodeMetrics | None = None

    # Para o sunburst: valor que define o tamanho do arco
    # Nos leaves = score_nexas, nos internos = soma dos filhos
    value: float | None = None

    # Filhos (vazio nos leaves)
    children: list[TreeNode] = []


class TreeResponse(BaseModel):
    """Resposta completa do endpoint /api/tree."""
    root: str                  # "AVALIAÇÃO DA ÁGUA | IQPA"
    contexto: TreeContexto
    tree: TreeNode


class TreeContexto(BaseModel):
    """Informações contextuais para o texto explicativo no frontend."""
    assunto_coluna: str
    pergunta_coluna: str
    onda: str
    direcao_filtro: str | None = None


# ============================================
# Schemas de filtros
# ============================================

class OndaResponse(BaseModel):
    """Uma onda disponível."""
    codigo: str
    descricao: str | None = None
    data_pesquisa: str | None = None
    total_registros: int | None = None


class FiltrosResponse(BaseModel):
    """Opções disponíveis para os dropdowns do frontend."""
    assuntos: list[str]
    perguntas: dict[str, list[str]]         # assunto → [perguntas]
    categorias: dict[str, list[str]]        # pergunta → [categorias]


class FiltrosPerguntasResponse(BaseModel):
    """Perguntas disponíveis para um assunto específico."""
    assunto: str
    perguntas: list[str]


class FiltrosCategoriasResponse(BaseModel):
    """Categorias disponíveis para uma pergunta específica."""
    pergunta: str
    categorias: list[str]


# ============================================
# Schemas de métricas resumidas
# ============================================

class MetricasResumo(BaseModel):
    """Painel de métricas do rodapé do dashboard."""
    total_cruzamentos: int
    total_drivers: int
    total_anti_drivers: int
    total_baixa_relevancia: int
    top_score: float
    top_categoria: str
    distribuicao_direcao: dict[str, int]    # "DRIVER FORTE": 120, etc.
