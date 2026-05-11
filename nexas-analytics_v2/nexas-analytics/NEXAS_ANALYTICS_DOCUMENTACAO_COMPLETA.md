# 📘 NEXAS ANALYTICS - DOCUMENTAÇÃO TÉCNICA COMPLETA

> **Versão:** 2.0  
> **Data:** Maio 2026  
> **Cliente:** Aegea Saneamento  
> **Objetivo:** Dashboard analítico para visualização de associações comportamentais via Lift Condicional

---

## 📋 ÍNDICE

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Estrutura de Pastas](#3-estrutura-de-pastas)
4. [Backend - Documentação Detalhada](#4-backend---documentação-detalhada)
5. [Frontend - Documentação Detalhada](#5-frontend---documentação-detalhada)
6. [Fluxo de Dados](#6-fluxo-de-dados)
7. [Glossário de Termos](#7-glossário-de-termos)
8. [Guia de Manutenção](#8-guia-de-manutenção)

---

## 1. VISÃO GERAL DO PROJETO

### 1.1 O Que é NEXAS Analytics?

NEXAS Analytics é um **dashboard analítico** que visualiza **associações comportamentais** entre perguntas de pesquisas de mercado usando a técnica de **Lift Condicional** (análise de cesta de mercado aplicada a surveys).

**Problema que resolve:**
- Analistas precisam identificar **quais respostas de uma pergunta estão associadas com outras respostas**
- Exemplo: "Quem avalia o serviço como ÓTIMO também tende a responder X em outra pergunta?"
- Detectar **drivers** (associações positivas) e **anti-drivers** (associações negativas)

**Solução:**
- Interface visual interativa (dendrograma horizontal)
- Métricas quantificadas (Score Nexas, Lift, Relevância)
- Exploração hierárquica de associações

---

### 1.2 Stack Tecnológica

**Backend:**
- **Python 3.10+**: Linguagem base
- **FastAPI**: Framework web assíncrono
- **SQLAlchemy**: ORM para banco de dados
- **SQLite**: Banco de dados (desenvolvimento)
- **Pydantic**: Validação de dados

**Frontend:**
- **HTML5 + CSS3**: Estrutura e estilo
- **JavaScript ES6**: Lógica
- **D3.js v7**: Visualização de dados
- **Vanilla JS**: Sem frameworks (simplicidade)

**DevOps:**
- **Pixi**: Gerenciador de ambientes Python
- **Uvicorn**: Servidor ASGI
- **Git**: Controle de versão

---

### 1.3 Modelo de Dados

**Entidades principais:**

```
Onda (survey wave)
  └── LiftResultado (cada linha = 1 associação entre 2 categorias)
      ├── Lado Coluna (pergunta sendo analisada)
      │   ├── ASSUNTO_COLUNA
      │   ├── PERGUNTA_COLUNA
      │   └── CATEGORIA_COLUNA
      ├── Lado Linha (respostas associadas)
      │   ├── ASSUNTO_LINHA
      │   ├── PERGUNTA_LINHA
      │   └── CATEGORIA_LINHA
      └── Métricas
          ├── LIFT (força da associação)
          ├── SCORE_NEXAS (lift × relevância)
          ├── DIRECAO (DRIVER/ANTI-DRIVER)
          └── PERCENTIL_RELEVANCIA
```

---

## 2. ARQUITETURA DO SISTEMA

### 2.1 Arquitetura Geral

```
┌─────────────────────────────────────────────────────────┐
│                     USUÁRIO (Analista)                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (SPA)                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  index.html (HTML + CSS + JavaScript + D3.js)   │   │
│  │  • Seleção de filtros (onda/assunto/pergunta)   │   │
│  │  • Dendrograma interativo                        │   │
│  │  • Tooltips com métricas                         │   │
│  │  • Controles (zoom, busca, export)               │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/JSON
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Routers (endpoints HTTP)                        │   │
│  │  • /api/ondas                                    │   │
│  │  • /api/assuntos                                 │   │
│  │  • /api/perguntas                                │   │
│  │  • /api/tree                                     │   │
│  └───────────────────┬─────────────────────────────┘   │
│                      ▼                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Services (lógica de negócio)                    │   │
│  │  • tree_builder: Constrói hierarquia            │   │
│  │  • aggregator: Calcula métricas                  │   │
│  └───────────────────┬─────────────────────────────┘   │
│                      ▼                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Models (ORM SQLAlchemy)                         │   │
│  │  • Onda                                          │   │
│  │  • LiftResultado                                 │   │
│  └───────────────────┬─────────────────────────────┘   │
│                      ▼                                   │
└────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              BANCO DE DADOS (SQLite)                     │
│  • nexas.db                                             │
│    ├── ondas                                            │
│    └── lift_resultados                                  │
└─────────────────────────────────────────────────────────┘
```

---

### 2.2 Padrão Arquitetural

**Arquitetura em Camadas (Layered Architecture):**

1. **Camada de Apresentação (Frontend)**
   - Interface do usuário
   - Lógica de visualização
   - Interação com usuário

2. **Camada de API (Routers)**
   - Recebe requests HTTP
   - Valida parâmetros
   - Delega para Services
   - Retorna responses JSON

3. **Camada de Negócio (Services)**
   - Lógica de domínio
   - Cálculos complexos
   - Regras de negócio

4. **Camada de Dados (Models + Database)**
   - Acesso ao banco
   - ORM (Object-Relational Mapping)
   - Persistência

**Por que essa arquitetura?**
- ✅ Separação de responsabilidades (Separation of Concerns)
- ✅ Testabilidade (cada camada pode ser testada isoladamente)
- ✅ Manutenibilidade (mudanças em uma camada não afetam outras)
- ✅ Escalabilidade (camadas podem ser escaladas independentemente)

---

## 3. ESTRUTURA DE PASTAS

```
nexas-analytics/
│
├── backend/                    # Código do servidor
│   ├── __init__.py
│   ├── main.py                 # Ponto de entrada da aplicação
│   ├── config.py               # Configurações (DB, CORS, etc.)
│   ├── database.py             # Sessão SQLAlchemy
│   │
│   ├── models/                 # ORM - Representação das tabelas
│   │   ├── __init__.py
│   │   └── lift.py             # Models: Onda, LiftResultado
│   │
│   ├── schemas/                # Pydantic - Validação de I/O
│   │   ├── __init__.py
│   │   └── tree.py             # Schemas: TreeNode, TreeResponse
│   │
│   ├── routers/                # Endpoints HTTP (controlers)
│   │   ├── __init__.py
│   │   ├── filtros.py          # GET /api/ondas, /api/assuntos, etc.
│   │   ├── tree.py             # GET /api/tree, /api/ramificacao
│   │   └── ingestao.py         # POST /api/ingest (upload Excel)
│   │
│   └── services/               # Lógica de negócio
│       ├── __init__.py
│       ├── tree_builder.py     # Constrói hierarquia do dendrograma
│       ├── aggregator.py       # Calcula agregações
│       └── excel_parser.py     # Parse de arquivos Excel
│
├── frontend/                   # Interface do usuário
│   └── index.html              # SPA completa (HTML + CSS + JS)
│
├── data/                       # Dados persistidos
│   └── nexas.db                # Banco SQLite
│
├── pixi.toml                   # Dependências Python
├── pixi.lock                   # Lock de versões
└── README.md                   # Instruções do projeto
```

---

### 3.1 Por Que Cada Pasta Existe?

#### **`backend/`**
Contém todo o código do servidor. Separado do frontend para permitir:
- Deploy independente
- Versionamento isolado
- Reutilização da API por outros clientes (mobile, CLI, etc.)

#### **`backend/models/`**
**O que:** Classes Python que representam tabelas do banco de dados (ORM).  
**Por que:** Abstração do SQL. Você trabalha com objetos Python em vez de escrever queries SQL manualmente.  
**Exemplo:** `Onda`, `LiftResultado`

#### **`backend/schemas/`**
**O que:** Classes Pydantic que definem estrutura de dados de entrada/saída da API.  
**Por que:** Validação automática + documentação automática (Swagger).  
**Diferença de Models:** Models = banco de dados, Schemas = API contracts.

#### **`backend/routers/`**
**O que:** Endpoints HTTP organizados por domínio funcional.  
**Por que:** Separação de responsabilidades. Cada router cuida de um conjunto de endpoints relacionados.  
**Analogia:** São os "controllers" do padrão MVC.

#### **`backend/services/`**
**O que:** Lógica de negócio pesada que não pertence aos routers.  
**Por que:** Routers devem ser finos (apenas receber request, chamar service, devolver response). Services concentram a lógica complexa.  
**Exemplo:** Construir a hierarquia do dendrograma (tree_builder.py) é complexo demais para estar num router.

#### **`frontend/`**
**O que:** Interface do usuário (Single Page Application).  
**Por que:** Separação física entre código de servidor e código de cliente. Facilita deploy em CDN se necessário.

#### **`data/`**
**O que:** Banco de dados SQLite.  
**Por que:** SQLite armazena tudo em um único arquivo. Essa pasta centraliza dados persistidos. Em produção, seria substituído por PostgreSQL/MySQL.

---

## 4. BACKEND - DOCUMENTAÇÃO DETALHADA

### 4.1 `backend/main.py`

**O que faz:** Ponto de entrada da aplicação FastAPI. Amarra todos os componentes.

**Responsabilidades:**
1. Criar instância do app FastAPI
2. Configurar CORS (quais domínios podem acessar a API)
3. Registrar routers (importar e incluir todos os endpoints)
4. Servir arquivos estáticos do frontend
5. Criar tabelas no banco na inicialização

**Código-chave:**

```python
# Criar aplicação
app = FastAPI(
    title="NEXAS Analytics",
    version="0.1.0",
    docs_url="/docs"  # Swagger UI em /docs
)

# CORS - permite frontend acessar API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # localhost:8000
    allow_methods=["*"],  # GET, POST, etc.
    allow_headers=["*"]   # Todos os headers
)

# Registrar endpoints
app.include_router(filtros.router)  # /api/ondas, /api/assuntos, etc.
app.include_router(tree.router)     # /api/tree, /api/ramificacao
app.include_router(ingestao.router) # /api/ingest

# Servir frontend
app.mount("/", StaticFiles(directory="frontend", html=True))
```

**Por que este arquivo existe?**
- Centraliza configuração
- Ponto único de entrada (`uvicorn backend.main:app`)
- Facilita testes (você importa `app` e testa)

---

### 4.2 `backend/config.py`

**O que faz:** Centraliza configurações da aplicação.

**Responsabilidades:**
1. Ler variáveis de ambiente
2. Definir defaults
3. Validar configurações na inicialização

**Variáveis principais:**

```python
class Settings(BaseSettings):
    app_env: str = "development"           # dev/staging/production
    app_port: int = 8000                   # Porta do servidor
    database_url: str = "sqlite:///..."    # URL do banco
    cors_origins: str = "http://localhost:8000"  # Domínios permitidos
```

**Por que existe?**
- Princípio: "Não hardcode valores"
- Facilita mudanças entre ambientes (dev/prod)
- Segurança (senhas não vão pro código)

---

### 4.3 `backend/database.py`

**O que faz:** Configura conexão com banco de dados via SQLAlchemy.

**Componentes:**

```python
# 1. Engine - conecta ao banco
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite específico
)

# 2. SessionLocal - factory de sessões
SessionLocal = sessionmaker(bind=engine)

# 3. Base - classe base para Models
Base = declarative_base()

# 4. Dependency Injection - fornece sessão aos endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db  # Endpoint usa a sessão
    finally:
        db.close()  # Fecha conexão
```

**Por que existe?**
- Centraliza configuração de DB
- Dependency Injection permite testar facilmente (mock de `get_db`)
- Garante que conexões sejam sempre fechadas (finally)

---

### 4.4 `backend/models/lift.py`

**O que faz:** Define estrutura das tabelas no banco (ORM).

**Classes:**

#### **`Onda`**
Representa uma onda de pesquisa (ex: "2025-Q1").

```python
class Onda(Base):
    __tablename__ = "ondas"
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String, unique=True)     # "2025-Q1"
    descricao = Column(String)               # "Primeiro trimestre 2025"
    data_pesquisa = Column(Date)             # Quando foi a pesquisa
    total_registros = Column(Integer)        # Quantos respondentes
    
    # Relacionamento 1:N com LiftResultado
    resultados = relationship("LiftResultado", back_populates="onda")
```

**Por que campos assim?**
- `codigo`: Identificador amigável (ex: "2025-Q1" vs ID numérico)
- `unique=True`: Garante que não há ondas duplicadas
- `relationship`: SQLAlchemy gerencia automaticamente joins

---

#### **`LiftResultado`**
Cada linha = 1 associação entre 2 categorias de perguntas.

```python
class LiftResultado(Base):
    __tablename__ = "lift_resultados"
    
    id = Column(Integer, primary_key=True)
    onda_id = Column(Integer, ForeignKey("ondas.id"))
    
    # Lado COLUNA (pergunta sendo analisada)
    assunto_coluna = Column(String)          # Ex: "AVALIAÇÃO DO SERVIÇO"
    pergunta_coluna = Column(String)         # Ex: "P1. Como você avalia?"
    categoria_coluna = Column(String)        # Ex: "ÓTIMO"
    
    # Lado LINHA (respostas associadas)
    assunto_linha = Column(String)
    pergunta_linha = Column(String)
    categoria_linha = Column(String)
    
    # Métricas
    lift = Column(Float)                     # Força da associação
    score_absoluto = Column(Float)           # Lift × base_comum
    score_relevancia = Column(Float)         # Lift × relevância
    direcao = Column(String)                 # "DRIVER" ou "ANTI-DRIVER"
    percentil_relevancia = Column(Float)     # 0 a 1
    
    # Bases (sample sizes)
    base_pergunta_comum = Column(Integer)    # N respondentes em comum
    base_cat_coluna = Column(Integer)
    base_cat_linha = Column(Integer)
    base_cat_comum = Column(Integer)
```

**Por que 6 colunas de texto?**
- Hierarquia: Assunto → Pergunta → Categoria
- 2 lados: Coluna (o que estamos analisando) vs Linha (associações)
- Flexibilidade: Permite cruzamentos arbitrários

**Por que tantas métricas?**
- `lift`: Métrica base (P(A|B) / P(A))
- `score_absoluto`: Lift ponderado pelo tamanho da amostra
- `score_relevancia`: **Score Nexas** = métrica principal (lift × relevância)
- `direcao`: Classificação categórica (facilita filtros)
- `percentil_relevancia`: Ranking relativo (top 10%, etc.)

---

### 4.5 `backend/schemas/tree.py`

**O que faz:** Define contratos da API (entrada/saída).

**Schemas principais:**

#### **`TreeNode`**
Representa um nó da árvore hierárquica.

```python
class TreeNode(BaseModel):
    name: str                        # Nome do nó
    leaf: bool = False               # É folha?
    metrics: TreeMetrics | None      # Métricas do nó
    children: list['TreeNode'] = []  # Filhos (recursivo)
```

**Por que recursivo?**
- Árvore = estrutura recursiva por natureza
- Permite profundidade arbitrária
- D3.js espera exatamente essa estrutura

---

#### **`TreeMetrics`**
Métricas de um nó.

```python
class TreeMetrics(BaseModel):
    # Folhas (leaf=True)
    score_nexas: float | None        # Score principal
    lift: float | None
    relevancia: float | None
    direcao: str | None              # DRIVER/ANTI-DRIVER
    categoria_direcao: str | None    # FORTE/MODERADO/FRACO
    base_comum: int | None
    
    # Nós internos (leaf=False)
    avg_score: float | None          # Média dos filhos
    min_score: float | None
    max_score: float | None
    median_score: float | None
    avg_relevancia: float | None
    count: int | None                # Quantos filhos
    
    # NOVO v2.0: Composição
    composition: dict | None         # {drivers: {...}, anti_drivers: {...}}
```

**Por que separar métricas de folhas vs nós internos?**
- Folhas: Dados originais do banco
- Nós internos: Agregações calculadas (média, mediana, etc.)
- `| None`: Permite campos opcionais (nem todo nó tem tudo)

---

#### **`TreeResponse`**
Response completo do endpoint `/api/tree`.

```python
class TreeResponse(BaseModel):
    tree: TreeNode              # Árvore hierárquica
    metadata: TreeMetadata      # Informações do cruzamento
```

**Por que separar tree e metadata?**
- Frontend precisa de contexto adicional
- Facilita cache (metadata não muda, tree sim)

---

### 4.6 `backend/routers/filtros.py`

**O que faz:** Endpoints que populam dropdowns do frontend.

**Endpoints:**

#### **`GET /api/ondas`**
Lista todas as ondas disponíveis.

```python
@router.get("/ondas", response_model=list[OndaResponse])
def listar_ondas(db: Session = Depends(get_db)):
    ondas = db.query(Onda).order_by(Onda.data_ingestao.desc()).all()
    return [OndaResponse(...) for o in ondas]
```

**Por que ordenar por data_ingestao desc?**
- Usuário geralmente quer ver dados mais recentes primeiro
- UX: dropdown já abre com onda atual selecionada

---

#### **`GET /api/assuntos?onda=X`**
Lista assuntos disponíveis para uma onda.

```python
@router.get("/assuntos")
def listar_assuntos(
    onda: str = Query(...),
    db: Session = Depends(get_db)
):
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
```

**Por que distinct?**
- Mesma coluna aparece em múltiplas linhas
- Queremos valores únicos para o dropdown

**Por que order_by?**
- Alfabético = mais fácil de encontrar

---

#### **`GET /api/perguntas?onda=X&assunto=Y`**
Lista perguntas de um assunto específico.

```python
@router.get("/perguntas")
def listar_perguntas_simples(
    onda: str = Query(...),
    assunto: str = Query(...),
    db: Session = Depends(get_db)
):
    # Validação
    onda_obj = db.query(Onda).filter_by(codigo=onda).first()
    if not onda_obj:
        return []
    
    # Query
    perguntas = [
        row[0] for row in
        db.query(distinct(LiftResultado.pergunta_coluna))
        .filter(
            LiftResultado.onda_id == onda_obj.id,
            LiftResultado.assunto_coluna == assunto
        )
        .order_by(LiftResultado.pergunta_coluna)
        .all()
    ]
    
    return perguntas
```

**Por que filtros em cascata?**
- Assunto → Pergunta é hierárquico
- Reduz opções a cada passo (melhor UX)
- Evita combinações inválidas

---

### 4.7 `backend/routers/tree.py`

**O que faz:** Endpoints de visualização (dendrograma).

#### **`GET /api/tree`**
Retorna árvore hierárquica completa.

```python
@router.get("/tree", response_model=TreeResponse)
def get_tree(
    onda: str = Query(...),
    assunto: str = Query(...),
    pergunta: str = Query(...),
    direcao: str | None = Query(None),        # Filtro opcional
    agregacao: str = Query("weighted_mean"),  # Como agregar nós internos
    db: Session = Depends(get_db)
):
    try:
        return build_tree(db, onda, assunto, pergunta, direcao, agregacao)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Parâmetros:**
- `onda`, `assunto`, `pergunta`: Definem o cruzamento
- `direcao`: Filtro opcional (só DRIVERS, só ANTI-DRIVERS, ou ambos)
- `agregacao`: Como calcular score dos nós internos
  - `weighted_mean`: Média ponderada pela relevância
  - `mean`: Média simples
  - `median`: Mediana
  - `max`: Máximo (potencial)

**Por que rodar build_tree num service?**
- Lógica complexa (~200 linhas)
- Reutilizável (outros endpoints podem chamar)
- Testável isoladamente

---

#### **`GET /api/ramificacao`**
Retorna subárvore de uma CATEGORIA_COLUNA específica.

```python
@router.get("/ramificacao", response_model=TreeNode)
def get_ramificacao(
    onda: str,
    assunto: str,
    pergunta: str,
    categoria: str,  # CATEGORIA_COLUNA específica
    direcao: str | None = None,
    db: Session = Depends(get_db)
):
    return build_ramificacao(db, onda, assunto, pergunta, categoria, direcao)
```

**Quando usar?**
- Usuário clica em um arco do sunburst → dendrograma mostra só aquele ramo
- Ctrl+Click em um nó nível 1 → abre nova aba focada naquele ramo

---

### 4.8 `backend/services/tree_builder.py`

**O que faz:** Constrói hierarquia do dendrograma a partir de dados planos do banco.

**Função principal:** `build_tree()`

#### **Algoritmo:**

```
1. Buscar dados do banco (flat table)
   └─> SELECT * FROM lift_resultados WHERE ...

2. Criar nó raiz
   └─> name = "ASSUNTO_COLUNA | PERGUNTA_COLUNA"

3. Agrupar por CATEGORIA_COLUNA (nível 1)
   └─> Para cada categoria única:
       ├─> Criar nó filho da raiz
       └─> Agrupar por ASSUNTO_LINHA (nível 2)
           └─> Para cada assunto_linha:
               ├─> Criar nó filho
               └─> Agrupar por PERGUNTA_LINHA (nível 3)
                   └─> Para cada pergunta_linha:
                       ├─> Criar nó filho
                       └─> Criar folhas (CATEGORIA_LINHA)

4. Calcular métricas agregadas de baixo para cima
   └─> Pós-ordem: folhas → raiz
       ├─> Folhas: métricas do banco
       └─> Nós internos: agregação dos filhos
```

**Código simplificado:**

```python
def build_tree(db, onda, assunto, pergunta, direcao, agregacao):
    # 1. Buscar dados
    resultados = (
        db.query(LiftResultado)
        .join(Onda)
        .filter(
            Onda.codigo == onda,
            LiftResultado.assunto_coluna == assunto,
            LiftResultado.pergunta_coluna == pergunta
        )
    )
    
    if direcao:
        resultados = resultados.filter(LiftResultado.direcao == direcao)
    
    resultados = resultados.all()
    
    # 2. Criar raiz
    root = TreeNode(
        name=f"{assunto} | {pergunta}",
        leaf=False,
        children=[]
    )
    
    # 3. Agrupar em hierarquia
    grupos_nivel1 = {}  # categoria_coluna -> linhas
    
    for r in resultados:
        cat = r.categoria_coluna
        if cat not in grupos_nivel1:
            grupos_nivel1[cat] = []
        grupos_nivel1[cat].append(r)
    
    # Para cada categoria_coluna (nível 1)
    for cat, linhas in grupos_nivel1.items():
        node_nivel1 = TreeNode(name=cat, leaf=False, children=[])
        
        # Agrupar por assunto_linha (nível 2)
        grupos_nivel2 = {}
        for r in linhas:
            assunto_l = r.assunto_linha
            if assunto_l not in grupos_nivel2:
                grupos_nivel2[assunto_l] = []
            grupos_nivel2[assunto_l].append(r)
        
        # ... repete para níveis 3 e 4 (pergunta_linha, categoria_linha)
        
        root.children.append(node_nivel1)
    
    # 4. Calcular agregações
    _calculate_aggregations(root, agregacao)
    
    return TreeResponse(tree=root, metadata=...)
```

**Por que recursivo?**
- Árvore = estrutura recursiva
- Código limpo e conciso
- Fácil adicionar/remover níveis

---

#### **`_calculate_aggregations()`**
Calcula métricas dos nós internos.

```python
def _calculate_aggregations(node, method):
    if node.leaf:
        return  # Folhas já têm métricas
    
    # Recursão: processa filhos primeiro (pós-ordem)
    for child in node.children:
        _calculate_aggregations(child, method)
    
    # Agrega métricas dos filhos
    scores = [get_score(c) for c in node.children]
    
    if method == "weighted_mean":
        weights = [c.metrics.relevancia for c in node.children]
        node.metrics.avg_score = weighted_mean(scores, weights)
    elif method == "mean":
        node.metrics.avg_score = mean(scores)
    elif method == "median":
        node.metrics.avg_score = median(scores)
    elif method == "max":
        node.metrics.avg_score = max(scores)
    
    node.metrics.min_score = min(scores)
    node.metrics.max_score = max(scores)
    node.metrics.count = len(node.children)
```

**Por que pós-ordem?**
- Precisa dos valores dos filhos para calcular o pai
- Garante que filhos são processados antes

---

#### **`_calculate_composition()` (v2.0)**
Calcula composição Driver/Anti-driver de nós internos.

```python
def _calculate_composition(node):
    if node.leaf:
        return None
    
    drivers = []
    anti_drivers = []
    
    # Coleta folhas recursivamente
    def collect_leaves(n):
        if n.leaf:
            if n.metrics.direcao == "DRIVER":
                drivers.append(n.metrics.score_nexas)
            elif n.metrics.direcao == "ANTI-DRIVER":
                anti_drivers.append(n.metrics.score_nexas)
        else:
            for child in n.children:
                collect_leaves(child)
    
    collect_leaves(node)
    
    total = len(drivers) + len(anti_drivers)
    if total == 0:
        return None
    
    composition = {}
    
    if drivers:
        composition["drivers"] = {
            "count": len(drivers),
            "percentage": round(len(drivers) / total * 100),
            "avg": mean(drivers),
            "max": max(drivers)
        }
    
    if anti_drivers:
        composition["anti_drivers"] = {
            "count": len(anti_drivers),
            "percentage": round(len(anti_drivers) / total * 100),
            "avg": mean(anti_drivers),
            "min": min(anti_drivers)
        }
    
    return composition
```

**Por que essa métrica é útil?**
- Nó interno pode ter mix de drivers/anti-drivers
- Composição mostra **distribuição interna**
- Ajuda analista entender **heterogeneidade** do ramo
- Exemplo: "REGULAR" = 60% drivers, 40% anti-drivers → ambivalente

**Por que não usar desvio padrão?**
- Desvio padrão mistura distribuições opostas (drivers +500, anti -400)
- Resultado não faz sentido (std alto pode ser bom ou ruim)
- Composição é interpretável: "60% positivo, 40% negativo"

---

### 4.9 `backend/services/aggregator.py`

**O que faz:** Funções auxiliares de agregação.

```python
def weighted_mean(values, weights):
    """Média ponderada."""
    if not values or not weights:
        return 0
    return sum(v * w for v, w in zip(values, weights)) / sum(weights)

def mean(values):
    """Média simples."""
    return sum(values) / len(values) if values else 0

def median(values):
    """Mediana."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0:
        return 0
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid-1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]
```

**Por que arquivo separado?**
- Reutilização (usadas em múltiplos lugares)
- Testabilidade (fácil testar funções puras)
- Manutenção (um lugar para adicionar novas agregações)

---

## 5. FRONTEND - DOCUMENTAÇÃO DETALHADA

### 5.1 Estrutura Geral

O frontend é um **SPA (Single Page Application)** completo em um único arquivo HTML.

**Seções:**
1. **HEAD** (~550 linhas): CSS completo
2. **BODY** (~250 linhas): HTML estrutura
3. **SCRIPT** (~1000 linhas): JavaScript lógica

---

### 5.2 Variáveis de Estado Global

```javascript
const state = {
    onda: null,           // Onda selecionada
    assunto: null,        // Assunto selecionado
    pergunta: null,       // Pergunta selecionada
    direcao: null,        // Filtro de direção (DRIVER/ANTI/null)
    treeData: null,       // Dados da árvore (cache)
    nodeYSpacing: 26,     // Espaçamento vertical entre nós
    nodeXSpacing: 220,    // Espaçamento horizontal entre níveis
    zoomLevel: 1,         // Nível de zoom atual
    agregacao: 'weighted_mean',  // Método de agregação
    isCompactMode: false  // Modo compacto ativo?
};
```

**Por que estado global?**
- Compartilhado entre funções
- Facilita debug (console.log(state))
- Permite save/restore (ex: localStorage)

---

### 5.3 Sistema de Cores Híbrido

**Conceito:**
- **Folhas (leaf nodes)**: Cor categórica por direção
  - 🟠 Driver: `#E8873D`
  - 🔵 Anti-driver: `#2E4A60`
  - ⚪ Neutro: `#6B7F8C`
  
- **Nós internos**: Cor por gradiente de score
  - Score -2000 → `#2E4A60` (azul escuro)
  - Score 0 → `#6B7F8C` (cinza)
  - Score +2000 → `#E8873D` (laranja)

**Implementação:**

```javascript
const COLOR_STOPS = [
    { score: -2000, color: '#2E4A60' },
    { score: -1000, color: '#4A7299' },
    { score: -200, color: '#5A8AB8' },
    { score: -30, color: '#6B7F8C' },
    { score: 30, color: '#9BB8A8' },
    { score: 200, color: '#D4A06A' },
    { score: 1000, color: '#E8873D' },
    { score: 2000, color: '#E8873D' }
];

function interpolateColor(score) {
    // Encontra stops ao redor do score
    for (let i = 0; i < COLOR_STOPS.length - 1; i++) {
        const stop1 = COLOR_STOPS[i];
        const stop2 = COLOR_STOPS[i + 1];
        
        if (score >= stop1.score && score <= stop2.score) {
            // Interpolação linear RGB
            const t = (score - stop1.score) / (stop2.score - stop1.score);
            const rgb1 = hexToRgb(stop1.color);
            const rgb2 = hexToRgb(stop2.color);
            
            const r = rgb1.r + t * (rgb2.r - rgb1.r);
            const g = rgb1.g + t * (rgb2.g - rgb1.g);
            const b = rgb1.b + t * (rgb2.b - rgb1.b);
            
            return rgbToHex(r, g, b);
        }
    }
    
    // Fora do range
    if (score < COLOR_STOPS[0].score) return COLOR_STOPS[0].color;
    return COLOR_STOPS[COLOR_STOPS.length - 1].color;
}

function nodeColor(d) {
    if (d.data.leaf) {
        // Folhas: cor categórica
        const dir = d.data.metrics.direcao;
        if (dir === 'DRIVER') return '#E8873D';
        if (dir === 'ANTI-DRIVER') return '#2E4A60';
        return '#6B7F8C';
    } else {
        // Nós internos: gradiente
        const score = getNodeScore(d);
        return interpolateColor(score);
    }
}
```

**Por que híbrido?**
- **Folhas categóricas**: Direção é absoluta (driver vs anti-driver)
- **Nós internos gradiente**: Score agregado é contínuo
- **Melhor interpretabilidade**: Folhas = classificação, nós = intensidade

---

### 5.4 Funções Principais

#### **`init()`**
Inicializa a aplicação.

```javascript
function init() {
    initTheme();              // Configura tema claro/escuro
    const urlState = loadFromURL();  // Lê parâmetros da URL
    loadOndas();              // Carrega dropdown de ondas
    
    // Event listeners
    document.getElementById('onda-select').addEventListener('change', onOndaChange);
    document.getElementById('assunto-select').addEventListener('change', onAssuntoChange);
    // ... mais listeners
}
```

**Por que separar init?**
- Garante que DOM está carregado antes
- Centraliza setup inicial
- Facilita testes (você pode chamar manualmente)

---

#### **`renderTree(data)`**
Renderiza o dendrograma com D3.js.

```javascript
function renderTree(data) {
    // 1. Limpar container
    const container = document.getElementById('svg-container');
    container.innerHTML = '';
    
    // 2. Criar SVG
    svg = d3.select('#svg-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    g = svg.append('g');  // Grupo para zoom/pan
    
    // 3. Configurar zoom
    const zoom = d3.zoom()
        .scaleExtent([0.1, 10])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    svg.call(zoom);
    
    // 4. Criar layout da árvore
    treemap = d3.tree()
        .nodeSize([state.nodeYSpacing, state.nodeXSpacing]);
    
    // 5. Transformar dados em hierarquia D3
    root = d3.hierarchy(data);
    root.x0 = height / 2;
    root.y0 = 0;
    
    // 6. Colapsar nós inicialmente
    root.children?.forEach(collapse);
    
    // 7. Primeira renderização
    update(root);
    
    // 8. Centralizar
    const initialTransform = d3.zoomIdentity
        .translate(100, height / 2)
        .scale(1);
    svg.call(zoom.transform, initialTransform);
}
```

**Por que D3.js?**
- Biblioteca padrão para visualizações de dados
- `d3.tree()`: Layout hierárquico pronto
- `d3.hierarchy()`: Converte JSON em estrutura D3
- `d3.zoom()`: Interação zoom/pan de graça

---

#### **`update(source)`**
Atualiza a árvore (chamada sempre que nó expande/colapsa).

```javascript
function update(source) {
    // 1. Recalcular posições
    const treeData = treemap(root);
    const nodes = treeData.descendants();
    const links = treeData.links();
    
    // 2. Ajustar posição X (horizontal = profundidade)
    nodes.forEach(d => { 
        d.y = d.depth * state.nodeXSpacing; 
    });
    
    // 3. Data binding (D3 pattern)
    const node = g.selectAll('g.node')
        .data(nodes, d => d.id || (d.id = ++i));
    
    // 4. ENTER: Novos nós
    const nodeEnter = node.enter().append('g')
        .attr('class', 'node')
        .attr('transform', d => `translate(${source.y0},${source.x0})`)
        .on('click', click)
        .on('mouseover', showTip)
        .on('mouseout', hideTip);
    
    nodeEnter.append('circle')
        .attr('r', 5)
        .style('fill', nodeColor);
    
    nodeEnter.append('text')
        .attr('dy', '.35em')
        .attr('x', d => d.children || d._children ? -10 : 10)
        .text(d => d.data.name);
    
    // 5. UPDATE: Nós existentes
    const nodeUpdate = nodeEnter.merge(node);
    nodeUpdate.transition()
        .duration(500)
        .attr('transform', d => `translate(${d.y},${d.x})`);
    
    // 6. EXIT: Nós removidos
    node.exit().transition()
        .duration(500)
        .attr('transform', d => `translate(${source.y},${source.x})`)
        .remove();
    
    // 7. Links (mesma lógica: enter, update, exit)
    // ...
}
```

**Por que padrão Enter-Update-Exit?**
- Padrão D3 para animações suaves
- Enter: elementos novos aparecem
- Update: elementos existentes se movem
- Exit: elementos removidos desaparecem

---

#### **`click(event, d)`**
Handler de click em nós.

```javascript
function click(event, d) {
    // Ctrl+Click → abre em nova aba
    if (event.ctrlKey || event.metaKey) {
        window.open(window.location.href, '_blank');
        return;
    }
    
    // Click normal → expande/colapsa
    if (d.children) {
        d._children = d.children;  // Guarda filhos
        d.children = null;          // Remove (colapsa)
    } else {
        d.children = d._children;  // Restaura filhos
        d._children = null;         // Limpa backup
    }
    
    update(d);  // Re-renderiza
}
```

**Por que `_children` vs `children`?**
- `children`: Filhos visíveis (D3 renderiza)
- `_children`: Filhos escondidos (D3 ignora)
- Trocar entre os dois = expandir/colapsar

---

#### **`collapse(d)` e `expand(d)`**
Colapsa/expande nós recursivamente.

```javascript
function collapse(d) {
    if (d.children) {
        d._children = d.children;
        d._children.forEach(collapse);  // Recursão
        d.children = null;
    }
}

function expand(d) {
    if (d._children) {
        d.children = d._children;
        d.children.forEach(expand);  // Recursão
        d._children = null;
    }
}
```

**Quando são chamadas?**
- Inicialização: `root.children.forEach(collapse)` (começa colapsado)
- Botão "Expandir tudo": `root.children.forEach(expand)`
- Botão "Colapsar tudo": `root.children.forEach(collapse)`

---

#### **`showTip(ev, d)`**
Exibe tooltip ao passar mouse sobre nó.

```javascript
function showTip(ev, d) {
    const m = d.data.metrics;
    const score = getNodeScore(d);
    
    let html = `<div class="t-title">${d.data.name}</div>`;
    
    if (d.data.leaf) {
        // Folhas: métricas originais
        html += `<div>Score: ${score.toFixed(2)}</div>`;
        html += `<div>Direção: ${m.direcao}</div>`;
        html += `<div>Lift: ${m.lift.toFixed(3)}</div>`;
    } else {
        // Nós internos: agregações
        html += `<div>Score Médio: ${score.toFixed(2)}</div>`;
        html += `<div>Range: ${m.min_score} a ${m.max_score}</div>`;
        
        // Composição (v2.0)
        if (m.composition) {
            html += `<div><strong>Composição:</strong></div>`;
            if (m.composition.drivers) {
                const d = m.composition.drivers;
                html += `<div>• Drivers: ${d.percentage}% (${d.count})</div>`;
                html += `<div>  média +${d.avg.toFixed(0)}, max +${d.max.toFixed(0)}</div>`;
            }
            if (m.composition.anti_drivers) {
                const a = m.composition.anti_drivers;
                html += `<div>• Anti-drivers: ${a.percentage}% (${a.count})</div>`;
                html += `<div>  média ${a.avg.toFixed(0)}, min ${a.min.toFixed(0)}</div>`;
            }
        }
    }
    
    html += `<div class="t-hint">💡 Ctrl+Click no nó para abrir em nova aba</div>`;
    
    tipEl.innerHTML = html;
    tipEl.style.opacity = '1';
    tipEl.style.left = `${ev.clientX + 16}px`;
    tipEl.style.top = `${ev.clientY - 10}px`;
}
```

**Por que separar lógica folha vs nó interno?**
- Métricas diferentes
- Evita poluição visual (não mostrar "composição" em folhas)

---

### 5.5 Features Especiais

#### **Modo Compacto (v2.0)**

**O que faz:**
- Minimiza header, esconde controles, maximiza espaço do dendrograma
- Header: 60px → 40px
- Contexto/Filtros/Métricas: 210px → 0px (escondidos)
- Toolbar: 50px (sempre visível)
- Total ganho: 180px

**Implementação:**

```javascript
function toggleCompactMode() {
    state.isCompactMode = !state.isCompactMode;
    document.body.classList.toggle('minimized', state.isCompactMode);
    
    // Atualiza botão
    document.getElementById('compact-icon').textContent = 
        state.isCompactMode ? '▼' : '▲';
    document.getElementById('compact-text').textContent = 
        state.isCompactMode ? 'Expandir' : 'Compacto';
}
```

**CSS:**

```css
.viz-wrapper {
    height: calc(100vh - 270px);  /* Modo normal */
}

body.minimized .viz-wrapper {
    height: calc(100vh - 90px);   /* Modo compacto */
}
```

**Por que essa feature?**
- Analistas passam 80% do tempo explorando o dendrograma
- Controles são usados no início, depois ficam inativos
- Sticky positioning permite modo compacto progressivo

---

#### **Overlay de Filtros**

**O que faz:**
- Quando minimizado, botão "⚙ Filtros" abre modal com controles
- Modal centralizado, backdrop blur
- Sincronização bidirecional com selects principais

**Por que overlay em vez de sidebar?**
- Perguntas têm nomes longos (>100 chars)
- Sidebar estreita quebraria texto de forma feia
- Modal tem espaço ilimitado

---

#### **Busca com Auto-expand**

```javascript
function searchNodes(query) {
    const matches = root.descendants()
        .filter(d => d.data.name.toLowerCase().includes(query));
    
    // Expande caminho até cada match
    matches.forEach(match => {
        let current = match;
        while (current) {
            if (current._children) {
                current.children = current._children;
                current._children = null;
            }
            current = current.parent;
        }
    });
    
    update(root);
    
    // Destaca matches
    g.selectAll('.node').each(function(d) {
        d3.select(this)
            .classed('highlighted', matches.includes(d))
            .classed('dimmed', !matches.includes(d));
    });
}
```

**Por que auto-expand?**
- Nó colapsado = invisível
- Usuário busca algo que está escondido → frustração
- Auto-expand garante que resultados são visíveis

---

## 6. FLUXO DE DADOS

### 6.1 Ingestão de Dados

```
Excel (.xlsx)
    ↓
[Upload via /api/ingest]
    ↓
excel_parser.py
    ├─> Valida colunas
    ├─> Parse de dados
    └─> Cria objetos SQLAlchemy
    ↓
Database (insert bulk)
    ↓
Onda + LiftResultado
```

---

### 6.2 Visualização de Dados

```
Frontend carrega
    ↓
GET /api/ondas
    ↓
[Usuário seleciona onda]
    ↓
GET /api/assuntos?onda=X
    ↓
[Usuário seleciona assunto]
    ↓
GET /api/perguntas?onda=X&assunto=Y
    ↓
[Usuário seleciona pergunta]
    ↓
GET /api/tree?onda=X&assunto=Y&pergunta=Z
    ↓
tree_builder.py
    ├─> Query banco (flat table)
    ├─> Agrupa em hierarquia
    ├─> Calcula agregações
    └─> Retorna TreeResponse (JSON)
    ↓
Frontend recebe JSON
    ↓
renderTree(data)
    ├─> d3.hierarchy(data)
    ├─> d3.tree().nodeSize()
    └─> update() → SVG
    ↓
Dendrograma renderizado
```

---

### 6.3 Interação do Usuário

```
[Usuário passa mouse sobre nó]
    ↓
showTip(event, node)
    ↓
Tooltip exibe métricas

[Usuário clica em nó]
    ↓
click(event, node)
    ├─> Se Ctrl+Click: abre nova aba
    └─> Se click: expande/colapsa
    ↓
update(node)
    ↓
SVG atualizado (animação)

[Usuário busca texto]
    ↓
searchNodes(query)
    ├─> Filtra nós por nome
    ├─> Auto-expande caminhos
    └─> Destaca matches
    ↓
SVG atualizado
```

---

## 7. GLOSSÁRIO DE TERMOS

### 7.1 Termos de Domínio

**Lift Condicional:**
- Técnica estatística de Market Basket Analysis adaptada para surveys
- Mede associação entre duas categorias de respostas
- Fórmula: `Lift = P(A|B) / P(A)`
  - Lift > 1: Associação positiva (B aumenta probabilidade de A)
  - Lift = 1: Independência (B não afeta A)
  - Lift < 1: Associação negativa (B reduz probabilidade de A)

**Score Nexas:**
- Métrica proprietária Aegea
- Pondera Lift pela relevância estatística
- Fórmula: `Score Nexas = Lift × Relevância × 1000`
- Range típico: -2000 a +2000

**Driver:**
- Associação positiva forte (Score Nexas > 30)
- Exemplo: "ÓTIMO" → "Recomendaria para amigos"

**Anti-driver:**
- Associação negativa forte (Score Nexas < -30)
- Exemplo: "PÉSSIMO" → "Já reclamou com órgãos"

**Relevância:**
- Percentil de relevância estatística (0 a 1)
- Baseado no tamanho da amostra
- Maior amostra = maior confiança = maior relevância

---

### 7.2 Termos Técnicos

**Onda:**
- Rodada de pesquisa (ex: "2025-Q1")
- Uma pesquisa pode ter múltiplas ondas ao longo do tempo

**Cruzamento:**
- Combinação de Assunto + Pergunta analisada
- Define qual dendrograma será gerado
- Exemplo: "AVALIAÇÃO DO SERVIÇO | P1. Como você avalia?"

**Hierarquia:**
- Estrutura em árvore do dendrograma
- 5 níveis: Root → Categoria Coluna → Assunto Linha → Pergunta Linha → Categoria Linha

**Agregação:**
- Método de calcular score de nós internos a partir dos filhos
- Weighted mean: Ponderada pela relevância (default)
- Mean: Média simples
- Median: Mediana (robusta a outliers)
- Max: Máximo (mostra potencial)

---

## 8. GUIA DE MANUTENÇÃO

### 8.1 Tarefas Comuns

#### **Adicionar novo campo ao banco**

1. Editar model em `backend/models/lift.py`:
```python
class LiftResultado(Base):
    # ... campos existentes
    novo_campo = Column(String)  # ADICIONAR AQUI
```

2. Criar migration (se usar Alembic):
```bash
alembic revision --autogenerate -m "add novo_campo"
alembic upgrade head
```

3. Atualizar schema em `backend/schemas/tree.py`:
```python
class TreeMetrics(BaseModel):
    # ... campos existentes
    novo_campo: str | None
```

4. Atualizar tree_builder para popular o campo:
```python
metrics = TreeMetrics(
    # ... campos existentes
    novo_campo=resultado.novo_campo
)
```

5. Atualizar frontend para exibir:
```javascript
if (m.novo_campo) {
    html += `<div>Novo: ${m.novo_campo}</div>`;
}
```

---

#### **Adicionar novo endpoint**

1. Criar função em router apropriado:
```python
# backend/routers/filtros.py

@router.get("/novo-endpoint")
def novo_endpoint(
    param: str = Query(...),
    db: Session = Depends(get_db)
):
    resultado = db.query(...).filter(...).all()
    return resultado
```

2. Frontend chama:
```javascript
async function chamarNovoEndpoint(param) {
    const resp = await fetch(`/api/novo-endpoint?param=${param}`);
    const data = await resp.json();
    return data;
}
```

---

#### **Adicionar nova feature no dendrograma**

1. Adicionar estado se necessário:
```javascript
const state = {
    // ... existente
    novaFeature: false
};
```

2. Adicionar controle no HTML:
```html
<button id="btn-nova-feature">Nova Feature</button>
```

3. Adicionar event listener:
```javascript
document.getElementById('btn-nova-feature')
    .addEventListener('click', () => {
        state.novaFeature = !state.novaFeature;
        update(root);  // Re-renderiza
    });
```

4. Implementar lógica em `update()`:
```javascript
if (state.novaFeature) {
    // Modifica renderização
}
```

---

### 8.2 Troubleshooting

#### **Dendrograma não renderiza**

1. Abrir DevTools Console (F12)
2. Procurar erros JavaScript
3. Verificar se dados chegaram:
```javascript
console.log('Tree data:', state.treeData);
```
4. Verificar se D3.js carregou:
```javascript
console.log('D3:', typeof d3);
```

---

#### **Endpoints retornam 404**

1. Verificar se router está registrado em `main.py`:
```python
app.include_router(nome_router.router)
```

2. Verificar prefix do router:
```python
router = APIRouter(prefix="/api", ...)
```

3. Testar no Swagger UI: `http://localhost:8000/docs`

---

#### **Banco de dados vazio**

1. Verificar se arquivo existe:
```bash
ls data/nexas.db
```

2. Verificar se tabelas foram criadas:
```bash
sqlite3 data/nexas.db ".tables"
```

3. Verificar se há dados:
```bash
sqlite3 data/nexas.db "SELECT COUNT(*) FROM lift_resultados;"
```

4. Se vazio, rodar ingestão:
```bash
# Via API
POST /api/ingest
# Arquivo Excel
```

---

### 8.3 Performance

#### **Query lenta**

1. Adicionar índice na coluna filtrada:
```python
class LiftResultado(Base):
    # ...
    assunto_coluna = Column(String, index=True)  # ADICIONAR index=True
```

2. Verificar query com EXPLAIN:
```python
query = db.query(LiftResultado).filter(...)
print(query.statement.compile(compile_kwargs={"literal_binds": True}))
```

3. Adicionar cache se query não muda:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_cached_data(onda, assunto):
    # ...
```

---

#### **Frontend lento**

1. Limitar número de nós visíveis:
```javascript
// Colapsar automaticamente ramos com >100 folhas
if (node.children && countLeaves(node) > 100) {
    collapse(node);
}
```

2. Desabilitar animações para árvores grandes:
```javascript
const duration = nodes.length > 500 ? 0 : 500;
nodeUpdate.transition().duration(duration);
```

3. Usar virtualização (renderizar só nós visíveis):
```javascript
// Mais complexo, considerar biblioteca como react-window
```

---

### 8.4 Debugging Tips

#### **Ver requests HTTP**

Abrir DevTools → Network → filtrar por "api"

#### **Ver dados no console**

```javascript
// Global state
window.DEBUG_STATE = state;
console.log(window.DEBUG_STATE);

// Tree data
console.log(JSON.stringify(state.treeData, null, 2));
```

#### **Ver SQL queries**

No backend, ativar logging SQLAlchemy:

```python
# config.py
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## 9. PRÓXIMOS PASSOS (Roadmap)

### 9.1 Features Planejadas

1. **Comparação Temporal**
   - Visualizar 2 ondas lado a lado
   - Detectar mudanças de tendência

2. **Filtro por Score Mínimo**
   - Slider para ocultar scores baixos
   - Focar apenas em associações fortes

3. **Export Interativo**
   - Export de subárvores específicas
   - Formatos: PNG, PDF, JSON

4. **Anotações Colaborativas**
   - Adicionar notas em nós
   - Compartilhar insights com equipe

5. **Sunburst View**
   - Visualização alternativa (radial)
   - Melhor para hierarquias largas

---

### 9.2 Melhorias Técnicas

1. **Migrar para PostgreSQL**
   - SQLite tem limitações de concorrência
   - Postgres permite múltiplos acessos simultâneos

2. **Adicionar Cache Redis**
   - Cache de queries frequentes
   - Reduz carga no banco

3. **Testes Automatizados**
   - Backend: pytest
   - Frontend: Jest + Testing Library

4. **CI/CD Pipeline**
   - GitHub Actions
   - Deploy automático após merge

5. **Monitoramento**
   - Sentry (error tracking)
   - DataDog (performance)

---

## 10. CONTATO E SUPORTE

**Desenvolvedor:**   
**Email:** 
**Repositório:** 

**Documentação de referência:**
- FastAPI: https://fastapi.tiangolo.com/
- D3.js: https://d3js.org/
- SQLAlchemy: https://docs.sqlalchemy.org/

---

**Última atualização:** Maio 2026  
**Versão da documentação:** 1.0
