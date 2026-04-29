-- ============================================
-- NEXAS Analytics — Schema do banco de dados
-- Versão: 001
-- Data: Abril 2026
-- ============================================

-- Tabela de metadados das ondas de pesquisa
CREATE TABLE IF NOT EXISTS ondas (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,          -- ex: "2025-Q1"
    descricao TEXT,                               -- ex: "Pesquisa Aegea 1º trimestre 2025"
    data_pesquisa DATE,                           -- data de referência da coleta
    data_ingestao TIMESTAMP DEFAULT NOW(),
    total_registros INTEGER,
    arquivo_origem VARCHAR(500)                   -- nome do XLSX original
);

-- Tabela principal de resultados do Lift Condicional
CREATE TABLE IF NOT EXISTS lift_resultados (
    id SERIAL PRIMARY KEY,

    -- Referência à onda
    onda_id INTEGER NOT NULL REFERENCES ondas(id) ON DELETE CASCADE,

    -- Cross 1 (coluna) — o indicador/pergunta-base sendo analisado
    assunto_coluna VARCHAR(200) NOT NULL,
    pergunta_coluna TEXT NOT NULL,
    categoria_coluna VARCHAR(300) NOT NULL,

    -- Cross 2 (linha) — as variáveis testadas como associadas
    assunto_linha VARCHAR(200) NOT NULL,
    pergunta_linha TEXT NOT NULL,
    categoria_linha VARCHAR(300) NOT NULL,

    -- Métricas de associação
    lift DECIMAL(12,6),                           -- Lift condicional (intensidade relativa)
    base_pergunta_comum INTEGER,                  -- Respondentes que responderam ambas
    base_cat_coluna INTEGER,                      -- Respondentes na categoria da coluna
    base_cat_linha INTEGER,                       -- Respondentes na categoria da linha
    base_cat_comum INTEGER,                       -- Respondentes em ambas as categorias

    -- Scores calculados
    score_relevancia DECIMAL(12,6),               -- Score Nexas (Score de Relevância)
    score_absoluto DECIMAL(12,6),                 -- Valor absoluto do score

    -- Classificação
    direcao VARCHAR(50),                          -- DRIVER, ANTI-DRIVER, BAIXA RELEVÂNCIA
    categoria_direcao VARCHAR(100),               -- DRIVER FORTE, DRIVER RELEVANTE, etc.
    rank_global INTEGER,                          -- Ranking global
    percentil_relevancia DECIMAL(8,6),            -- Percentil (0 a 1)
    ranking_final VARCHAR(100)                    -- TOP ABSOLUTO, CLASSIFICAÇÃO MEDIANA, etc.
);

-- ============================================
-- ÍNDICES
-- ============================================

-- Filtro principal: o analista escolhe assunto + pergunta + categoria
CREATE INDEX idx_filtro_principal
    ON lift_resultados(onda_id, assunto_coluna, pergunta_coluna, categoria_coluna);

-- Filtro por direção (DRIVER / ANTI-DRIVER)
CREATE INDEX idx_direcao
    ON lift_resultados(onda_id, direcao, categoria_direcao);

-- Navegação por assunto_linha (nível 2 do dendrograma)
CREATE INDEX idx_assunto_linha
    ON lift_resultados(onda_id, assunto_linha);

-- Busca por score (ordenação por relevância)
CREATE INDEX idx_score
    ON lift_resultados(onda_id, score_relevancia DESC);
