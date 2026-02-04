-- ============================================================================
-- QUERY 1: Top 5 Operadoras com Maior Crescimento (%)
-- Comparação: Primeiro Trimestre (Min) vs Último Trimestre (Max)
-- ============================================================================

WITH limites_temporais AS (
    -- 1. Descobre dinamicamente qual é o primeiro e o último período disponível
    SELECT 
        MIN(ano * 10 + trimestre) as periodo_min,
        MAX(ano * 10 + trimestre) as periodo_max
    FROM despesas_eventos
),
despesas_inicio AS (
    -- 2. Calcula despesa total de cada operadora no PRIMEIRO período
    SELECT d.registro_ans, SUM(d.valor) as total_inicial
    FROM despesas_eventos d, limites_temporais l
    WHERE (d.ano * 10 + d.trimestre) = l.periodo_min
    GROUP BY d.registro_ans
),
despesas_fim AS (
    -- 3. Calcula despesa total de cada operadora no ÚLTIMO período
    SELECT d.registro_ans, SUM(d.valor) as total_final
    FROM despesas_eventos d, limites_temporais l
    WHERE (d.ano * 10 + d.trimestre) = l.periodo_max
    GROUP BY d.registro_ans
)
SELECT 
    o.razao_social,
    di.total_inicial,
    df.total_final,
    -- Cálculo de Crescimento: ((Final - Inicial) / Inicial) * 100
    ROUND(((df.total_final - di.total_inicial) / di.total_inicial) * 100, 2) as crescimento_percentual
FROM operadoras o
JOIN despesas_inicio di ON o.registro_ans = di.registro_ans
JOIN despesas_fim df ON o.registro_ans = df.registro_ans
WHERE di.total_inicial > 0 -- Evita divisão por zero
ORDER BY 4 DESC -- Ordena pelo crescimento (4ª coluna)
LIMIT 5;

-- ============================================================================
-- QUERY 2: Distribuição Geográfica (Top 5 UFs)
-- Métricas: Total Absoluto e Média por Operadora Ativa
-- ============================================================================

SELECT 
    o.uf,
    -- Total de despesas no estado
    SUM(d.valor) as despesa_total_estado,
    -- Contagem distinta (Operadoras que realmente tiveram operação)
    COUNT(DISTINCT o.registro_ans) as qtd_operadoras_ativas,
    -- Média real (Total / Quem gastou)
    ROUND(SUM(d.valor) / COUNT(DISTINCT o.registro_ans), 2) as media_por_operadora
FROM despesas_eventos d
JOIN operadoras o ON d.registro_ans = o.registro_ans
GROUP BY o.uf
ORDER BY despesa_total_estado DESC
LIMIT 5;

-- ============================================================================
-- QUERY 3: Performance Consistente (Acima da Média)
-- ============================================================================

WITH metricas_trimestrais AS (
    -- 1. AGREGAÇÃO: Transforma as milhares de linhas contábeis em 
    -- UMA linha de total por Operadora/Trimestre.
    SELECT 
        ano, 
        trimestre, 
        registro_ans, -- Agrupamos pela CHAVE PRIMÁRIA, não pelo nome
        SUM(valor) as total_op
    FROM despesas_eventos
    GROUP BY ano, trimestre, registro_ans
),
media_mercado AS (
    -- 2. Calcula a média do mercado para cada trimestre
    SELECT 
        ano, 
        trimestre,
        AVG(total_op) as media_geral_mercado
    FROM metricas_trimestrais
    GROUP BY ano, trimestre
),
performance_individual AS (
    -- 3. Compara cada operadora contra a média daquele trimestre específico
    SELECT 
        mt.registro_ans,
        mt.ano,
        mt.trimestre,
        CASE WHEN mt.total_op > mm.media_geral_mercado THEN 1 ELSE 0 END as acima_media
    FROM metricas_trimestrais mt
    JOIN media_mercado mm ON mt.ano = mm.ano AND mt.trimestre = mm.trimestre
)
SELECT 
    o.registro_ans, -- Identificador único (evita somar operadoras diferentes)
    o.razao_social,
    SUM(pi.acima_media) as qtd_trimestres_acima
FROM performance_individual pi
JOIN operadoras o ON pi.registro_ans = o.registro_ans
GROUP BY o.registro_ans, o.razao_social
HAVING SUM(pi.acima_media) >= 2 -- Filtro: Pelo menos 2 trimestres acima da média
ORDER BY qtd_trimestres_acima DESC, o.razao_social;