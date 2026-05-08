# NEXAS Analytics — Documentação de Continuidade

**Última atualização:** 04/05/2026  
**Status:** Sistema operacional com 98.929 registros carregados  
**Stack:** FastAPI + SQLite + D3.js Collapsible Tree

---

## 1. Estado Atual do Projeto

### O que está funcionando
✅ Backend FastAPI completo com 5 endpoints REST  
✅ Ingestão de XLSX (98.929 registros) em ~2 segundos  
✅ SQLite funcionando com índices e foreign keys  
✅ Frontend com dendrograma D3 Collapsible Tree  
✅ Controles de zoom (＋/－/Fit)  
✅ Sliders X (120-400px) e Y (14-100px) para espaçamento  
✅ Busca visual de nós por texto  
✅ Expandir/Colapsar tudo  
✅ Tema dark/light com toggle persistente  
✅ Tooltips com métricas detalhadas  
✅ CSS separado em `frontend/css/style.css`  
✅ Configuração Pixi opcional (ambiente reprodutível)

### Problemas conhecidos resolvidos
- ❌ ~~PostgreSQL connection refused~~ → Migrado para SQLite
- ❌ ~~SQL DISTINCT error~~ → Corrigido com `.group_by()`
- ❌ ~~Event listeners acumulando nos sliders~~ → Movidos para `initControls()` (chamado UMA VEZ)
- ❌ ~~Texto sobrepondo nós~~ → Implementada quebra automática em 36 caracteres

---

## 2. Estrutura de Arquivos

```
nexas-analytics/
├── backend/
│   ├── config.py              # Pydantic Settings (lê .env)
│   ├── database.py            # Engine SQLite/PostgreSQL + sessões
│   ├── main.py                # FastAPI app (amarra routers, serve frontend)
│   ├── models/
│   │   └── lift.py            # SQLAlchemy: Onda + LiftResultado
│   ├── schemas/
│   │   └── tree.py            # Pydantic: TreeNode, LeafMetrics, NodeMetrics
│   ├── services/
│   │   ├── ingestor.py        # Lê XLSX, valida, bulk insert (chunks de 5000)
│   │   ├── tree_builder.py    # Transforma flat SQL → JSON hierárquico (5 níveis)
│   │   └── aggregator.py      # Métricas resumidas
│   └── routers/
│       ├── filtros.py         # GET /api/ondas, /api/filtros (cascata de dropdowns)
│       ├── tree.py            # GET /api/tree, /api/metricas
│       └── ingestao.py        # POST /api/ingestao/upload (futuro)
├── frontend/
│   ├── index.html             # SPA com D3 Collapsible Tree
│   └── css/
│       └── style.css          # Estilos separados (temas dark/light)
├── scripts/
│   ├── ingest_cli.py          # CLI de ingestão (integra create_tables)
│   └── create_db.py           # Cria tabelas SQLite
├── migrations/
│   └── 001_create_tables.sql  # Schema versionado
├── dados/
│   ├── nexas.db               # Banco SQLite (não versionado)
│   └── .gitkeep
├── pixi.toml                  # Configuração Pixi (ambiente reprodutível)
├── requirements.txt           # Deps Python (psycopg2 comentado)
├── .env.example               # Template de configuração
├── .gitignore                 # Ignora .pixi/, dados/*.db, dados/*.xlsx
└── README.md                  # Setup com Pixi (primário) ou venv (alternativa)
```

---

## 3. Endpoints da API

| Método | Endpoint | Descrição | Params |
|--------|----------|-----------|--------|
| `GET` | `/api/ondas` | Lista ondas disponíveis | — |
| `GET` | `/api/filtros` | Assuntos, perguntas, categorias | `onda` |
| `GET` | `/api/tree` | Árvore hierárquica completa | `onda`, `assunto`, `pergunta`, `direcao` (opcional) |
| `GET` | `/api/metricas` | Resumo: total drivers/anti, top score, distribuição | `onda`, `assunto`, `pergunta`, `direcao` (opcional) |
| `GET` | `/api/health` | Health check | — |

---

## 4. Hierarquia dos Dados

### XLSX entrada (BASE_LIFT)
98.929 linhas × 18 colunas

**Cross 1 (coluna):**
- `ASSUNTO_COLUNA`
- `PERGUNTA_COLUNA`
- `CATEGORIA_COLUNA`

**Cross 2 (linha):**
- `ASSUNTO_LINHA`
- `PERGUNTA_LINHA`
- `CATEGORIA_LINHA`

**Métricas:**
- `LIFT`
- `Score Nexas` (métrica principal)
- `DIREÇÃO`
- `CATEGORIA DA DIREÇÃO`
- `Percentil de Relevância`
- `Rank`

### Hierarquia renderizada (5 níveis)
```
Root (0):  ASSUNTO_COLUNA | PERGUNTA_COLUNA
  ├─ N1:   CATEGORIA_COLUNA
  │  ├─ N2:   ASSUNTO_LINHA
  │  │  ├─ N3:   PERGUNTA_LINHA
  │  │  │  └─ N4 (leaf): CATEGORIA_LINHA
  │  │  │     [lift, score_nexas, direcao, base_comum]
```

Nós internos recebem métricas agregadas (avg_score, avg_relevancia, count).

---

## 5. Como Rodar (Comandos Rápidos)

### Setup inicial

```powershell
cd C:\vanessa\code\nexas-analytics\nexas-analytics_v2\nexas-analytics

# Opção 1: Pixi (recomendado)
pixi install
pixi run ingest "dados\WORKBOOK_ANALISE_VERSAO_INICIAL 2.xlsx" --onda 2025-Q1
pixi run serve

# Opção 2: Conda (atual)
conda activate nexas
copy .env.example .env
python -m scripts.ingest_cli "dados\WORKBOOK_ANALISE_VERSAO_INICIAL 2.xlsx" --onda 2025-Q1
uvicorn backend.main:app --reload --port 8000
```

Acessa `http://localhost:8000`

---

## 6. Configuração Crítica

### .env (mínimo necessário)
```env
DATABASE_URL=sqlite:///dados/nexas.db
APP_ENV=development
APP_PORT=8000
```

### database.py — Detecção automática SQLite/PostgreSQL
```python
def _build_engine(url: str) -> Engine:
    if url.startswith('sqlite'):
        return create_engine(
            url,
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
        )
    else:
        return create_engine(url, pool_pre_ping=True)
```

---

## 7. Frontend — Controles do Dendrograma

### Arquitetura de event listeners (CRÍTICO)
**NÃO registrar controles dentro de `renderTree()`** — isso acumula handlers duplicados.

**CORRETO:**
```javascript
// Chamado UMA VEZ em init()
function initControls() {
    document.getElementById('slider-y').addEventListener('input', () => {
        layout.spacingY = +sliderY.value;
        recalcLayout();  // usa doUpdate global
    });
}

// Expõe update globalmente
function renderTree(data) {
    // ... setup SVG ...
    doUpdate = function update(source) { /* ... */ };
    doUpdate(rootNode);
}
```

**ERRADO:**
```javascript
function renderTree(data) {
    slider.addEventListener('input', () => { ... });  // ❌ ACUMULA
}
```

### Controles disponíveis
| Controle | Elemento | Range | Função |
|----------|----------|-------|--------|
| Zoom In | `#btn-zoom-in` | — | `zoomBeh.scaleBy(1.3)` |
| Zoom Out | `#btn-zoom-out` | — | `zoomBeh.scaleBy(0.77)` |
| Zoom Fit | `#btn-zoom-fit` | — | `fitToScreen()` |
| Espaço Y | `#slider-y` | 14-100px | Recalcula altura SVG + `doUpdate()` |
| Espaço X | `#slider-x` | 120-400px | `d.y = d.depth * spacingX` |
| Busca | `#search-box` | — | Destaca nós com `.highlighted` |
| Expandir tudo | `#btn-expand` | — | `d.children = d._children` recursivo |
| Colapsar tudo | `#btn-collapse` | — | `d._children = d.children` (depth > 0) |

### Variáveis CSS customizáveis
Arquivo: `frontend/css/style.css`

```css
[data-theme="dark"] {
    --driver-forte:   #E8873D;  /* Laranja */
    --driver-rel:     #D4A06A;  /* Marrom claro */
    --driver-mod:     #7A9BB8;  /* Azul acinzentado */
    --anti-driver:    #4A7299;  /* Azul médio */
    --baixa:          #2E4A60;  /* Azul escuro */
    --link-default:   rgba(46,107,158,0.30);
    --node-stroke:    #2E6B9E;
    --bg-primary:     #0A1628;
    /* ... */
}
```

---

## 8. Problemas Comuns & Soluções

### "SQL DISTINCT error"
**Causa:** SQLite não aceita `distinct()` dentro de `with_entities()`.  
**Solução:** Usar `.group_by()` em vez de `distinct()`.

```python
# ❌ ERRADO (gera SQL inválido no SQLite)
.with_entities(LiftResultado.assunto_coluna, distinct(LiftResultado.pergunta_coluna))

# ✅ CORRETO
.with_entities(LiftResultado.assunto_coluna, LiftResultado.pergunta_coluna)
.group_by(LiftResultado.assunto_coluna, LiftResultado.pergunta_coluna)
```

### "Sliders não respondem após trocar cruzamento"
**Causa:** Event listeners registrados dentro de `renderTree()` acumulam.  
**Solução:** Mover todos os `addEventListener` para `initControls()` (ver seção 7).

### "PostgreSQL connection refused"
**Causa:** `.env` aponta pra PostgreSQL mas Postgres não está instalado.  
**Solução:** Garantir `DATABASE_URL=sqlite:///dados/nexas.db` no `.env`.

### "Texto sobrepondo nos nós"
**Causa:** Labels longos sem quebra de linha.  
**Solução:** Função `wrapText(text, 36)` já implementada — quebra automaticamente em 36 caracteres.

---

## 9. Próximas Melhorias (Roadmap)

### Fase 2 — Exportação
- [ ] Botão "Exportar PNG" (usa `html2canvas` ou `saveSvgAsPng`)
- [ ] Botão "Exportar SVG" (download direto do SVG)
- [ ] Exportar tabela de leaves em CSV

### Fase 3 — Comparativo Temporal
- [ ] Endpoint `/api/compare?onda1=X&onda2=Y`
- [ ] Visual de diferença (delta de scores entre ondas)
- [ ] Heatmap de mudanças ao longo do tempo

### Fase 4 — Produção
- [ ] Migração para PostgreSQL (mudar 1 linha no `.env`)
- [ ] Docker Compose (FastAPI + Postgres + Nginx)
- [ ] Autenticação (login com email/senha)
- [ ] Multi-tenancy (cada cliente vê só seus dados)

---

## 10. Comandos de Desenvolvimento

```powershell
# Rodar servidor (hot reload)
pixi run serve
# ou
uvicorn backend.main:app --reload --port 8000

# Ingerir novo XLSX
pixi run ingest "dados\arquivo.xlsx" --onda 2026-Q2
# ou
python -m scripts.ingest_cli "dados\arquivo.xlsx" --onda 2026-Q2

# Resetar banco (apaga tudo e recria)
pixi run create-db
# ou
python -m scripts.create_db

# Testes (quando implementados)
pixi run -e dev test
# ou
pytest backend/tests/ -v

# Ver logs SQL (development mode)
# Já habilitado quando APP_ENV=development no .env
```

---

## 11. Dados de Teste

**Arquivo:** `dados/WORKBOOK_ANALISE_VERSAO_INICIAL 2.xlsx`  
**Registros:** 98.929 cruzamentos  
**Onda:** `2025-Q1`

**Distribuição:**
- Drivers: 32.473 (32,8%)
- Anti-drivers: 19.868 (20,1%)
- Baixa relevância: 46.588 (47,1%)

**Cruzamento exemplo para teste:**
- Assunto: `ATENDIMENTO`
- Pergunta: `P46. Como você avalia os serviços prestados pela concessionária?`
- Categorias: `ÓTIMO`, `BOM`, `REGULAR`, `RUIM`, `PÉSSIMO`

---

## 12. Variáveis de Estado Globais (Frontend)

```javascript
// Layout configurável via sliders
const layout = { spacingY: 26, spacingX: 220 };

// Referências D3 (expostas por renderTree)
let svgEl = null;           // elemento <svg>
let gTree = null;           // grupo principal <g>
let zoomBeh = null;         // d3.zoom() behavior
let rootNode = null;        // d3.hierarchy root
let doUpdate = null;        // função update() — chamada pelos controles
let currentTreemap = null;  // d3.tree() — reutilizado em recalcLayout()

// State da aplicação
const state = {
    onda: null,
    assunto: null,
    pergunta: null,
    direcao: null  // 'DRIVER', 'ANTI-DRIVER', ou null
};
```

---

## 13. Como Continuar em Nova Conversa

### Cole este prompt inicial:

```
Estou continuando o projeto NEXAS Analytics. É um dashboard FastAPI + SQLite + D3.js 
para visualizar associações (Lift Condicional) de pesquisa de mercado como dendrograma.

Estado atual:
- Backend funcionando com 98.929 registros carregados
- Frontend com dendrograma D3 Collapsible Tree operacional
- Controles de zoom e espaçamento (X/Y sliders) funcionando
- CSS separado em frontend/css/style.css

Arquivos principais:
- backend/main.py (FastAPI)
- backend/routers/tree.py (endpoint /api/tree)
- frontend/index.html (D3 + controles)
- frontend/css/style.css (temas dark/light)

Preciso de ajuda com: [DESCREVA O PROBLEMA AQUI]
```

### Anexe sempre:
1. **Este documento** (`CONTINUIDADE.md`)
2. **Print da tela** se houver bug visual
3. **Erro completo do console** se houver erro de código
4. **Arquivo relevante** se for correção específica (ex: `tree.py` se o problema for no backend)

---

## 14. Contatos Técnicos

**Desenvolvedor:** Vanessa (Geógrafa USP + MBA Ciência de Dados + IA Poli-USP)  
**Cliente:** Aegea Saneamento  
**Ambiente de desenvolvimento:** Windows 11 + Conda/Pixi  
**Localização do projeto:** `C:\vanessa\code\nexas-analytics\nexas-analytics_v2\nexas-analytics`

---

## 15. Checklist de Handoff

Antes de iniciar nova conversa, confirme:

- [ ] O servidor está rodando sem erros (`uvicorn backend.main:app --reload`)
- [ ] Os 98.929 registros estão carregados (`SELECT COUNT(*) FROM lift_resultados;`)
- [ ] O frontend abre no browser (`http://localhost:8000`)
- [ ] Você consegue selecionar onda → assunto → pergunta e ver o dendrograma
- [ ] Os sliders X e Y respondem (sem bug de acúmulo de handlers)
- [ ] Você tem a última versão de `index.html` e `style.css` (ver seção 2)

Se qualquer item falhar, **descreva exatamente qual** na nova conversa.

---

**Última revisão:** 04/05/2026 18:58 BRT  
**Versão:** 1.0.0
