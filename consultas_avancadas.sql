-- ═══════════════════════════════════════════════════════════════════════════
--  E-COMMERCE DE CARROS — CONSULTAS SQL AVANÇADAS
--  Banco   : ecommerce_carros.db (SQLite)
--  Tabela  : anuncios
--  Colunas : id, marca_modelo, ano_fabricacao, preco_brl,
--            data_anuncio, combustivel, status
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
--  BLOCO 1 ▸ GROUP BY
-- ───────────────────────────────────────────────────────────────────────────

-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 1.1 Preço médio, mediano (aprox.) e total de anúncios por marca/modelo  │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    marca_modelo,
    COUNT(*)                        AS total_anuncios,
    ROUND(AVG(preco_brl), 2)        AS preco_medio,
    ROUND(MIN(preco_brl), 2)        AS preco_minimo,
    ROUND(MAX(preco_brl), 2)        AS preco_maximo,
    ROUND(MAX(preco_brl)
        - MIN(preco_brl), 2)        AS amplitude_preco
FROM anuncios
GROUP BY marca_modelo
ORDER BY preco_medio DESC;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 1.2 Quantidade de anúncios por ano de fabricação + % sobre o total      │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    ano_fabricacao,
    COUNT(*)                                         AS total_anuncios,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2
    )                                                AS pct_do_total,
    ROUND(AVG(preco_brl), 2)                         AS preco_medio
FROM anuncios
GROUP BY ano_fabricacao
ORDER BY ano_fabricacao;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 1.3 Resumo por combustível — ticket médio e participação no estoque     │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    combustivel,
    COUNT(*)                                          AS qtd,
    ROUND(AVG(preco_brl), 2)                          AS preco_medio,
    ROUND(MIN(preco_brl), 2)                          AS preco_min,
    ROUND(MAX(preco_brl), 2)                          AS preco_max,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_estoque
FROM anuncios
GROUP BY combustivel
ORDER BY preco_medio DESC;


-- ───────────────────────────────────────────────────────────────────────────
--  BLOCO 2 ▸ CTEs / TABELAS DERIVADAS (simulando JOINs)
-- ───────────────────────────────────────────────────────────────────────────

-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 2.1 Segmentação por faixa de preço + JOIN com tabela principal          │
-- │     Faixas: Econômico · Intermediário · Premium · Luxo                  │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH faixas AS (
    SELECT
        id,
        preco_brl,
        CASE
            WHEN preco_brl <  50000              THEN '1_Econômico'
            WHEN preco_brl >= 50000
             AND preco_brl <  90000              THEN '2_Intermediário'
            WHEN preco_brl >= 90000
             AND preco_brl < 130000              THEN '3_Premium'
            ELSE                                      '4_Luxo'
        END AS faixa_preco
    FROM anuncios
)
SELECT
    a.marca_modelo,
    a.ano_fabricacao,
    a.combustivel,
    a.status,
    ROUND(a.preco_brl, 2)   AS preco_brl,
    f.faixa_preco
FROM anuncios  a
JOIN faixas    f ON a.id = f.id
ORDER BY a.preco_brl DESC
LIMIT 50;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 2.2 Distribuição de anúncios e preço médio por faixa de preço          │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH faixas AS (
    SELECT
        id,
        CASE
            WHEN preco_brl <  50000 THEN '1_Econômico'
            WHEN preco_brl <  90000 THEN '2_Intermediário'
            WHEN preco_brl < 130000 THEN '3_Premium'
            ELSE                         '4_Luxo'
        END AS faixa_preco
    FROM anuncios
)
SELECT
    f.faixa_preco,
    COUNT(*)                                           AS total,
    ROUND(AVG(a.preco_brl), 2)                         AS preco_medio,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM anuncios a
JOIN faixas   f ON a.id = f.id
GROUP BY f.faixa_preco
ORDER BY f.faixa_preco;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 2.3 Comparação do preço de cada veículo contra a média de sua faixa     │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH faixas AS (
    SELECT
        id,
        preco_brl,
        CASE
            WHEN preco_brl <  50000 THEN '1_Econômico'
            WHEN preco_brl <  90000 THEN '2_Intermediário'
            WHEN preco_brl < 130000 THEN '3_Premium'
            ELSE                         '4_Luxo'
        END AS faixa_preco
    FROM anuncios
),
media_faixa AS (
    SELECT
        faixa_preco,
        ROUND(AVG(preco_brl), 2) AS media_da_faixa
    FROM faixas
    GROUP BY faixa_preco
)
SELECT
    a.marca_modelo,
    a.combustivel,
    ROUND(a.preco_brl, 2)                              AS preco_brl,
    f.faixa_preco,
    mf.media_da_faixa,
    ROUND(a.preco_brl - mf.media_da_faixa, 2)          AS desvio_da_media,
    CASE
        WHEN a.preco_brl > mf.media_da_faixa THEN 'Acima da média'
        ELSE                                      'Abaixo da média'
    END AS posicao_relativa
FROM anuncios    a
JOIN faixas      f  ON a.id = f.id
JOIN media_faixa mf ON f.faixa_preco = mf.faixa_preco
ORDER BY f.faixa_preco, desvio_da_media DESC
LIMIT 60;


-- ───────────────────────────────────────────────────────────────────────────
--  BLOCO 3 ▸ WINDOW FUNCTIONS
-- ───────────────────────────────────────────────────────────────────────────

-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 3.1 Ranking dos veículos mais caros por marca (RANK e DENSE_RANK)       │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH marcas AS (
    -- Extrai apenas a primeira palavra como marca
    SELECT
        *,
        SUBSTR(marca_modelo, 1, INSTR(marca_modelo || ' ', ' ') - 1) AS marca
    FROM anuncios
)
SELECT
    marca,
    marca_modelo,
    ano_fabricacao,
    combustivel,
    ROUND(preco_brl, 2)                                   AS preco_brl,
    RANK()       OVER (PARTITION BY marca ORDER BY preco_brl DESC) AS rank_preco,
    DENSE_RANK() OVER (PARTITION BY marca ORDER BY preco_brl DESC) AS dense_rank_preco,
    ROW_NUMBER() OVER (PARTITION BY marca ORDER BY preco_brl DESC) AS row_num
FROM marcas
QUALIFY rank_preco <= 3   -- Top 3 mais caros por marca (SQLite ≥ 3.45 / use subquery abaixo)
ORDER BY marca, rank_preco;

-- ► Alternativa compatível com SQLite < 3.45 (sem QUALIFY):
WITH marcas AS (
    SELECT
        *,
        SUBSTR(marca_modelo, 1, INSTR(marca_modelo || ' ', ' ') - 1) AS marca
    FROM anuncios
),
rankeds AS (
    SELECT
        marca,
        marca_modelo,
        ano_fabricacao,
        combustivel,
        ROUND(preco_brl, 2)                                        AS preco_brl,
        RANK() OVER (PARTITION BY marca ORDER BY preco_brl DESC)   AS rank_preco
    FROM marcas
)
SELECT *
FROM rankeds
WHERE rank_preco <= 3
ORDER BY marca, rank_preco;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 3.2 Média móvel de 7 registros do preço (ordenado por data de anúncio)  │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    id,
    marca_modelo,
    data_anuncio,
    ROUND(preco_brl, 2)                                        AS preco_brl,
    ROUND(
        AVG(preco_brl) OVER (
            ORDER BY data_anuncio, id
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    )                                                          AS media_movel_7,
    ROUND(
        AVG(preco_brl) OVER (
            ORDER BY data_anuncio, id
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ), 2
    )                                                          AS media_movel_30
FROM anuncios
ORDER BY data_anuncio, id
LIMIT 100;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 3.3 Percentil de preço com PERCENT_RANK e NTILE (quartis)               │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    id,
    marca_modelo,
    combustivel,
    ROUND(preco_brl, 2)                             AS preco_brl,
    ROUND(
        PERCENT_RANK() OVER (ORDER BY preco_brl), 4
    )                                               AS percent_rank,
    NTILE(4) OVER (ORDER BY preco_brl)              AS quartil,
    NTILE(10) OVER (ORDER BY preco_brl)             AS decil,
    -- Rótulo legível do quartil
    CASE NTILE(4) OVER (ORDER BY preco_brl)
        WHEN 1 THEN 'Q1 — Mais baratos'
        WHEN 2 THEN 'Q2 — Abaixo da mediana'
        WHEN 3 THEN 'Q3 — Acima da mediana'
        WHEN 4 THEN 'Q4 — Mais caros'
    END                                             AS quartil_label
FROM anuncios
ORDER BY preco_brl DESC
LIMIT 80;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 3.4 Diferença do preço em relação ao anterior e próximo (LAG / LEAD)    │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    id,
    marca_modelo,
    data_anuncio,
    ROUND(preco_brl, 2)                                       AS preco_brl,
    ROUND(LAG(preco_brl)  OVER (ORDER BY data_anuncio, id), 2) AS preco_anterior,
    ROUND(LEAD(preco_brl) OVER (ORDER BY data_anuncio, id), 2) AS preco_proximo,
    ROUND(preco_brl
        - LAG(preco_brl) OVER (ORDER BY data_anuncio, id), 2)  AS delta_anterior,
    ROUND(
        (preco_brl - LAG(preco_brl) OVER (ORDER BY data_anuncio, id))
        * 100.0
        / NULLIF(LAG(preco_brl) OVER (ORDER BY data_anuncio, id), 0)
    , 2)                                                       AS variacao_pct
FROM anuncios
ORDER BY data_anuncio, id
LIMIT 60;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 3.5 Acumulado de receita potencial (SUM acumulado) ordenado por data    │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    id,
    data_anuncio,
    marca_modelo,
    ROUND(preco_brl, 2)                                          AS preco_brl,
    ROUND(
        SUM(preco_brl) OVER (
            ORDER BY data_anuncio, id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    )                                                            AS receita_acumulada,
    COUNT(*) OVER (
        ORDER BY data_anuncio, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                                            AS anuncios_acumulados
FROM anuncios
ORDER BY data_anuncio, id
LIMIT 80;


-- ───────────────────────────────────────────────────────────────────────────
--  BLOCO 4 ▸ CONSULTAS ANALÍTICAS
-- ───────────────────────────────────────────────────────────────────────────

-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 4.1 Top 5 veículos mais caros por categoria de combustível              │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH ranked_comb AS (
    SELECT
        combustivel,
        marca_modelo,
        ano_fabricacao,
        status,
        ROUND(preco_brl, 2)                                          AS preco_brl,
        ROW_NUMBER() OVER (
            PARTITION BY combustivel
            ORDER BY preco_brl DESC
        )                                                            AS rn
    FROM anuncios
)
SELECT
    combustivel,
    rn          AS posicao,
    marca_modelo,
    ano_fabricacao,
    status,
    preco_brl
FROM ranked_comb
WHERE rn <= 5
ORDER BY combustivel, rn;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 4.2 Evolução temporal do preço médio — agrupado por ano e mês           │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    STRFTIME('%Y', data_anuncio)                                  AS ano,
    STRFTIME('%m', data_anuncio)                                  AS mes,
    STRFTIME('%Y-%m', data_anuncio)                               AS ano_mes,
    COUNT(*)                                                      AS total_anuncios,
    ROUND(AVG(preco_brl), 2)                                      AS preco_medio,
    ROUND(MIN(preco_brl), 2)                                      AS preco_min,
    ROUND(MAX(preco_brl), 2)                                      AS preco_max,
    -- Variação do preço médio em relação ao mês anterior
    ROUND(
        AVG(preco_brl)
        - LAG(AVG(preco_brl)) OVER (ORDER BY STRFTIME('%Y-%m', data_anuncio))
    , 2)                                                          AS variacao_vs_mes_anterior
FROM anuncios
GROUP BY STRFTIME('%Y-%m', data_anuncio)
ORDER BY ano_mes;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 4.3 Preço médio anual por combustível (tabela pivô via CASE)            │
-- └─────────────────────────────────────────────────────────────────────────┘
SELECT
    STRFTIME('%Y', data_anuncio)                         AS ano,
    ROUND(AVG(CASE WHEN combustivel = 'Gasolina' THEN preco_brl END), 2) AS media_gasolina,
    ROUND(AVG(CASE WHEN combustivel = 'Flex'     THEN preco_brl END), 2) AS media_flex,
    ROUND(AVG(CASE WHEN combustivel = 'Diesel'   THEN preco_brl END), 2) AS media_diesel,
    ROUND(AVG(CASE WHEN combustivel = 'Elétrico' THEN preco_brl END), 2) AS media_eletrico,
    ROUND(AVG(CASE WHEN combustivel = 'Híbrido'  THEN preco_brl END), 2) AS media_hibrido,
    ROUND(AVG(preco_brl), 2)                                             AS media_geral
FROM anuncios
GROUP BY ano
ORDER BY ano;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 4.4 Análise de status por faixa de preço — taxa de conversão (vendidos) │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH faixas AS (
    SELECT
        id,
        status,
        CASE
            WHEN preco_brl <  50000 THEN '1_Econômico'
            WHEN preco_brl <  90000 THEN '2_Intermediário'
            WHEN preco_brl < 130000 THEN '3_Premium'
            ELSE                         '4_Luxo'
        END AS faixa_preco
    FROM anuncios
)
SELECT
    faixa_preco,
    COUNT(*)                                                      AS total,
    SUM(CASE WHEN status = 'Vendido'    THEN 1 ELSE 0 END)        AS vendidos,
    SUM(CASE WHEN status = 'Disponível' THEN 1 ELSE 0 END)        AS disponiveis,
    SUM(CASE WHEN status = 'Reservado'  THEN 1 ELSE 0 END)        AS reservados,
    ROUND(
        SUM(CASE WHEN status = 'Vendido' THEN 1.0 ELSE 0 END)
        / COUNT(*) * 100, 1
    )                                                             AS taxa_venda_pct
FROM faixas
GROUP BY faixa_preco
ORDER BY faixa_preco;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 4.5 Score composto: veículos com melhor custo-benefício                 │
-- │     (preço abaixo da média da marca + ano recente + disponível)         │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH media_marca AS (
    SELECT
        marca_modelo,
        ROUND(AVG(preco_brl), 2) AS preco_medio_modelo
    FROM anuncios
    GROUP BY marca_modelo
)
SELECT
    a.id,
    a.marca_modelo,
    a.ano_fabricacao,
    a.combustivel,
    ROUND(a.preco_brl, 2)             AS preco_brl,
    mm.preco_medio_modelo,
    ROUND(
        (mm.preco_medio_modelo - a.preco_brl)
        / mm.preco_medio_modelo * 100, 1
    )                                 AS desconto_vs_media_pct,
    -- Score: % de desconto + bônus por ano recente
    ROUND(
        ( (mm.preco_medio_modelo - a.preco_brl) / mm.preco_medio_modelo * 100 )
        + (a.ano_fabricacao - 2010) * 0.5
    , 2)                              AS score_custo_beneficio
FROM anuncios    a
JOIN media_marca mm ON a.marca_modelo = mm.marca_modelo
WHERE a.status = 'Disponível'
  AND a.preco_brl < mm.preco_medio_modelo
ORDER BY score_custo_beneficio DESC
LIMIT 20;


-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ 4.6 Outliers de preço — valores além de 2 desvios-padrão da média       │
-- └─────────────────────────────────────────────────────────────────────────┘
WITH estatisticas AS (
    SELECT
        AVG(preco_brl)                              AS media,
        -- Desvio padrão (SQLite não tem STDEV nativo; calculado manualmente)
        SQRT(AVG(preco_brl * preco_brl)
             - AVG(preco_brl) * AVG(preco_brl))     AS desvio_padrao
    FROM anuncios
)
SELECT
    a.id,
    a.marca_modelo,
    a.combustivel,
    ROUND(a.preco_brl, 2)                           AS preco_brl,
    ROUND(e.media, 2)                               AS media_geral,
    ROUND(e.desvio_padrao, 2)                       AS desvio_padrao,
    ROUND(
        (a.preco_brl - e.media) / e.desvio_padrao, 2
    )                                               AS z_score,
    CASE
        WHEN a.preco_brl > e.media + 2 * e.desvio_padrao THEN 'Outlier alto'
        WHEN a.preco_brl < e.media - 2 * e.desvio_padrao THEN 'Outlier baixo'
    END                                             AS tipo_outlier
FROM anuncios a
CROSS JOIN estatisticas e
WHERE ABS(a.preco_brl - e.media) > 2 * e.desvio_padrao
ORDER BY z_score DESC;
