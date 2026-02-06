-- ============================================================================
-- PARTE 1: ESTRUTURA DOS DADOS (DDL)
-- Recria as tabelas limpas e otimizadas
-- ============================================================================

-- Limpeza inicial (apenas se for admin)
DROP TABLE IF EXISTS despesas_agregadas;
DROP TABLE IF EXISTS despesas_eventos;
DROP TABLE IF EXISTS operadoras;

-- 1. TABELA MÃE (Dimensão): OPERADORAS
CREATE TABLE operadoras (
    registro_ans VARCHAR(10) PRIMARY KEY,
    cnpj VARCHAR(20) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100),
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    nome_fantasia VARCHAR(255),
    logradouro VARCHAR(255),
    numero VARCHAR(50),
    complemento VARCHAR(255),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf VARCHAR(2),
    cep VARCHAR(20),
    ddd VARCHAR(5),
    telefone VARCHAR(50),
    fax VARCHAR(50),
    endereco_eletronico VARCHAR(255),
    representante VARCHAR(255),
    cargo_representante VARCHAR(255),
    regiao_comercializacao VARCHAR(50),
    data_registro_ans VARCHAR(50)
);
CREATE INDEX idx_ops_uf ON operadoras(uf);
CREATE INDEX idx_ops_razao ON operadoras(razao_social); -- Importante para o ILIKE da IA

-- 2. TABELA FILHA (Fato Transacional): DESPESAS_EVENTOS
CREATE TABLE despesas_eventos (
    id BIGSERIAL PRIMARY KEY,
    registro_ans VARCHAR(10) NOT NULL,
    ano INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    conta_contabil VARCHAR(50),
    descricao VARCHAR(255),
    valor NUMERIC(18, 2) NOT NULL,
    
    CONSTRAINT fk_evento_operadora
        FOREIGN KEY (registro_ans) REFERENCES operadoras(registro_ans)
        ON DELETE CASCADE
);
CREATE INDEX idx_eventos_tempo ON despesas_eventos(ano, trimestre);
CREATE INDEX idx_eventos_fk ON despesas_eventos(registro_ans);

-- 3. TABELA FILHA (Fato Analítico): DESPESAS_AGREGADAS
CREATE TABLE despesas_agregadas (
    id SERIAL PRIMARY KEY,
    registro_ans VARCHAR(10) NOT NULL,
    total_despesas NUMERIC(18, 2),
    media_trimestral NUMERIC(18, 2),
    desvio_padrao NUMERIC(18, 2),
    qtde_trimestres INTEGER,
    data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_agregada_operadora
        FOREIGN KEY (registro_ans) REFERENCES operadoras(registro_ans)
        ON DELETE CASCADE
);

-- ============================================================================
-- PARTE 2: SEGURANÇA E PERMISSÕES (DCL)
-- Aqui criamos o "Cofre" para a IA
-- ============================================================================

-- 1. Cria o usuário específico (se não existir)

SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'reader';

-- Agora sim podemos deletar sem erro de "dependência" ou "sessão ativa"
DROP OWNED BY reader;
DROP ROLE IF EXISTS reader;

-- Cria do zero com a senha correta
CREATE ROLE reader WITH LOGIN PASSWORD '{DB_READER_PWD}';

-- 2. Garante que ele pode conectar no banco
GRANT CONNECT ON DATABASE postgres TO reader; 

-- 3. Garante acesso ao esquema public (onde estão as tabelas)
GRANT USAGE ON SCHEMA public TO reader;

-- 4. O "Pulo do Gato": Dá SELECT em TUDO, mas WRITE em NADA.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reader;

-- 5. Segurança Futura: Se você criar tabelas novas amanhã, 
-- esse usuário automaticamente ganha acesso de leitura nelas (mas não escrita).
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reader;

-- 6. (Opcional) Revoga permissões perigosas caso tenham sido dadas acidentalmente
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER 
ON ALL TABLES IN SCHEMA public FROM reader;

-- 7. Garante que o reader não pode criar outros roles
ALTER ROLE reader NOCREATEROLE;

-- 8. Garante que o reader não pode criar bancos de dados
ALTER ROLE reader NOCREATEDB;

-- 9. CRUCIAL: Garante que o reader não é superusuário
ALTER ROLE reader NOSUPERUSER;

-- 10. CRUCIAL: Impede que o reader herde permissões de outros
ALTER ROLE reader NOINHERIT;