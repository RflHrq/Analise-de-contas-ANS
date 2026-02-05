import sys
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Importação dos Serviços e Schemas
from api.services.ai_analyst import process_user_query 
from api.schemas import (
    OperadoraSimples, 
    PaginatedOperadoras, 
    DespesaDetalhe, 
    DashboardStorytelling
)

# --- Configuração de Caminho e Imports Locais ---
# Adiciona a raiz do projeto ao Python Path para importar o config.py corretamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DATABASE_URL_READER

# --- Configuração do Banco de Dados ---
try:
    # USANDO USUÁRIO LEITOR PARA SEGURANÇA NA API
    engine = create_engine(DATABASE_URL_READER, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Erro fatal ao conectar no banco: {e}")
    sys.exit(1)

# Dependência (Dependency Injection) para gestão de sessão
def get_db():
    """
    Gerenciador de contexto para criar e fechar sessões do banco de dados.
    Garante que a conexão seja encerrada corretamente após o uso na requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Inicialização da Aplicação ---
app = FastAPI(
    title="API ANS - Despesas de Operadoras",
    description="API REST para consulta de dados financeiros e contábeis de operadoras de saúde.",
    version="1.0.0"
)

# Configuração de CORS (Permite acesso do Frontend Vue.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# ROTA 1: Listagem de Operadoras
# ==============================================================================
@app.get("/api/operadoras", response_model=PaginatedOperadoras)
def list_operadoras(
    page: int = Query(1, ge=1, description="Número da página atual"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(None, description="Termo de busca (Razão Social ou CNPJ)"),
    db: Session = Depends(get_db)
):
    """
    Lista as operadoras de saúde cadastradas com paginação e filtros.

    Argumentos:
        page (int): Número da página a ser recuperada.
        limit (int): Quantidade de registros por página.
        search (str, optional): Texto para busca por Razão Social ou CNPJ.
        db (Session): Sessão do banco de dados.

    Retorna:
        dict: Dicionário contendo o total de registros, página atual, limite e a lista de operadoras.
    """
    offset = (page - 1) * limit
    params = {'limit': limit, 'offset': offset}

    # Construção da Query Base
    base_query = "FROM operadoras"
    where_clause = ""

    # Aplicação de Filtro (Busca Textual - Case Insensitive)
    if search:
        where_clause = " WHERE razao_social ILIKE :search OR cnpj ILIKE :search"
        params['search'] = f"%{search}%"

    # 1. Query de Contagem (Total de registros para a paginação)
    count_sql = text(f"SELECT COUNT(*) {base_query} {where_clause}")
    total = db.execute(count_sql, params).scalar()

    # 2. Query de Dados (Registros da página)
    # Seleciona apenas os campos necessários para a listagem
    data_sql = text(f"""
        SELECT registro_ans, cnpj, razao_social, modalidade, uf 
        {base_query} {where_clause}
        ORDER BY razao_social 
        LIMIT :limit OFFSET :offset
    """)
    result = db.execute(data_sql, params).fetchall()

    # Mapeamento manual para garantir integridade com o Schema Pydantic
    operadoras_list = [
        OperadoraSimples(
            registro_ans=row.registro_ans, 
            cnpj=row.cnpj, 
            razao_social=row.razao_social, 
            modalidade=row.modalidade, 
            uf=row.uf
        ) for row in result
    ]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": operadoras_list
    }

# ==============================================================================
# ROTA 2: Histórico de Despesas de uma Operadora
# ==============================================================================
@app.get("/api/operadoras/{cnpj}/despesas", response_model=List[DespesaDetalhe])
def get_despesas_operadora(cnpj: str, db: Session = Depends(get_db)):
    """
    Consulta o histórico detalhado de despesas de uma operadora específica pelo CNPJ.
    
    Argumentos:
        cnpj (str): O CNPJ da operadora.
        db (Session): Sessão do banco de dados.
        
    Retorna:
        list: Lista de despesas contendo ano, trimestre, conta contábil, descrição e valor.
    """
    # 1. Busca o ID (RegistroANS) através do CNPJ
    op_query = text("SELECT registro_ans FROM operadoras WHERE cnpj = :cnpj")
    op = db.execute(op_query, {'cnpj': cnpj}).fetchone()
    
    if not op:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")

    # 2. Busca as despesas vinculadas a esse ID
    desp_query = text("""
        SELECT ano, trimestre, conta_contabil, descricao, valor
        FROM despesas_eventos
        WHERE registro_ans = :registro_ans
        ORDER BY ano DESC, trimestre DESC, valor DESC
    """)
    
    result = db.execute(desp_query, {'registro_ans': op.registro_ans}).fetchall()
    
    return result

# ==============================================================================
# NOVA ROTA: Detalhes da Operadora (Por CNPJ)
# ==============================================================================
@app.get("/api/operadoras/{cnpj}", response_model=OperadoraSimples)
def get_operadora_detalhes(cnpj: str, db: Session = Depends(get_db)):
    """
    Retorna os dados cadastrais de uma operadora específica.
    """
    query = text("""
        SELECT registro_ans, cnpj, razao_social, modalidade, uf 
        FROM operadoras 
        WHERE cnpj = :cnpj
    """)
    result = db.execute(query, {'cnpj': cnpj}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
        
    return OperadoraSimples(
        registro_ans=result.registro_ans,
        cnpj=result.cnpj,
        razao_social=result.razao_social,
        modalidade=result.modalidade,
        uf=result.uf
    )

from api.schemas import EstatisticasGerais

# ==============================================================================
# NOVA ROTA: Estatísticas Gerais (Agregado)
# ==============================================================================
@app.get("/api/estatisticas", response_model=EstatisticasGerais)
def get_estatisticas(db: Session = Depends(get_db)):
    """
    Retorna estatísticas agregadas do sistema:
    - Total de Despesas
    - Média por Operadora
    - Top 5 Operadoras (Maiores Despesas Totais)
    """
    
    # 1. Totais e Média
    kpi_query = text("SELECT SUM(valor) as total, COUNT(DISTINCT registro_ans) as qtd FROM despesas_eventos")
    row = db.execute(kpi_query).fetchone()
    
    total = row.total or 0.0
    qtd = row.qtd or 1
    media = total / qtd if qtd > 0 else 0.0
    
    # 2. Top 5 Operadoras (Por Volume Total)
    top_query = text("""
        SELECT o.razao_social, SUM(d.valor) as total
        FROM despesas_eventos d
        JOIN operadoras o ON d.registro_ans = o.registro_ans
        GROUP BY o.razao_social
        ORDER BY total DESC
        LIMIT 5
    """)
    top_rows = db.execute(top_query).fetchall()
    top_5 = [{"razao_social": r.razao_social, "total": r.total} for r in top_rows]

    # 3. Distribuição UF (Extra para preencher o schema)
    uf_query = text("""
        SELECT o.uf, SUM(d.valor) as total
        FROM despesas_eventos d
        JOIN operadoras o ON d.registro_ans = o.registro_ans
        WHERE o.uf IS NOT NULL
        GROUP BY o.uf
        ORDER BY total DESC
    """)
    uf_rows = db.execute(uf_query).fetchall()
    dist_uf = [{"uf": r.uf, "total": r.total} for r in uf_rows]
    
    return EstatisticasGerais(
        total_mercado=total,
        media_por_operadora=media,
        top_5_operadoras=top_5,
        distribuicao_uf=dist_uf
    )

# ==============================================================================
# ROTA 3: Dashboard (Analytics)
# ==============================================================================
@app.get("/api/analytics/storytelling", response_model=DashboardStorytelling)
def get_storytelling(db: Session = Depends(get_db)):
    """
    Gera um relatório analítico complexo (Storytelling) com os principais KPIs.
    
    Calcula:
        1. Métricas Macro (Total, Média, Tendência).
        2. Top Movers (Operadoras com maior crescimento).
        3. Geo Eficiência (Desempenho por Estado).
        4. Consistência (Operadoras recorrentemente acima da média).

    Retorna:
        DashboardStorytelling: Objeto com todas as métricas calculadas.
    """
    
    # 1. KPIs MACRO (Tendência e Atividade)
    kpi_query = text("""
        WITH limites AS (
            SELECT MIN(ano*10+trimestre) as min_p, MAX(ano*10+trimestre) as max_p 
            FROM despesas_eventos
        ),
        valores AS (
            SELECT 
                SUM(d.valor) as total_geral,
                COUNT(DISTINCT d.registro_ans) as ativas,
                SUM(CASE WHEN (d.ano*10+d.trimestre) = l.min_p THEN d.valor ELSE 0 END) as valor_inicio,
                SUM(CASE WHEN (d.ano*10+d.trimestre) = l.max_p THEN d.valor ELSE 0 END) as valor_fim
            FROM despesas_eventos d, limites l
        )
        SELECT total_geral, ativas, valor_inicio, valor_fim FROM valores
    """)
    kpi_row = db.execute(kpi_query).fetchone()
    
    # Tratamento de Nulos para evitar erros matemáticos
    total_geral = kpi_row.total_geral or 0.0
    ativas = kpi_row.ativas or 0
    valor_inicio = kpi_row.valor_inicio or 0.0
    valor_fim = kpi_row.valor_fim or 0.0

    tendencia = 0.0
    if valor_inicio > 0:
        tendencia = ((valor_fim - valor_inicio) / valor_inicio) * 100

    media_geral = 0.0
    if ativas > 0:
        media_geral = total_geral / ativas

    # 2. TOP MOVERS (Crescimento)
    # Identifica operadoras com maior crescimento percentual no período
    movers_query = text("""
        WITH limites AS (
            SELECT MIN(ano*10+trimestre) as min_p, MAX(ano*10+trimestre) as max_p 
            FROM despesas_eventos
        ),
        inicio AS (
            SELECT d.registro_ans, SUM(d.valor) as v_ini 
            FROM despesas_eventos d, limites l 
            WHERE (d.ano*10+d.trimestre)=l.min_p 
            GROUP BY d.registro_ans
        ),
        fim AS (
            SELECT d.registro_ans, SUM(d.valor) as v_fim 
            FROM despesas_eventos d, limites l 
            WHERE (d.ano*10+d.trimestre)=l.max_p 
            GROUP BY d.registro_ans
        )
        SELECT 
            o.razao_social, 
            f.v_fim, 
            ROUND(((f.v_fim - i.v_ini)/i.v_ini)*100, 2) as cresc
        FROM operadoras o 
        JOIN inicio i ON o.registro_ans = i.registro_ans 
        JOIN fim f ON o.registro_ans = f.registro_ans
        WHERE i.v_ini > 0 
        ORDER BY 3 DESC 
        LIMIT 5
    """)
    movers = db.execute(movers_query).fetchall()

    # 3. GEO EFICIÊNCIA (Ranking por UF)
    geo_query = text("""
        SELECT 
            o.uf, 
            SUM(d.valor) as total, 
            COUNT(DISTINCT o.registro_ans) as qtd, 
            SUM(d.valor)/COUNT(DISTINCT o.registro_ans) as media
        FROM despesas_eventos d 
        JOIN operadoras o ON d.registro_ans = o.registro_ans
        WHERE o.uf IS NOT NULL 
        GROUP BY o.uf 
        ORDER BY total DESC 
        LIMIT 10
    """)
    geo = db.execute(geo_query).fetchall()

    # 4. CONSISTÊNCIA (Operadoras consistentemente acima da média)
    consistency_query = text("""
        WITH metricas AS (
            SELECT ano, trimestre, registro_ans, SUM(valor) as total 
            FROM despesas_eventos 
            GROUP BY ano, trimestre, registro_ans
        ),
        medias AS (
            SELECT ano, trimestre, AVG(total) as m_geral 
            FROM metricas 
            GROUP BY ano, trimestre
        ),
        perf AS (
            SELECT mt.registro_ans, 
            CASE WHEN mt.total > mm.m_geral THEN 1 ELSE 0 END as win 
            FROM metricas mt 
            JOIN medias mm ON mt.ano=mm.ano AND mt.trimestre=mm.trimestre
        )
        SELECT o.razao_social, o.uf, SUM(p.win) as qtd 
        FROM perf p 
        JOIN operadoras o ON p.registro_ans = o.registro_ans
        WHERE o.razao_social NOT ILIKE '%INATIVA%' 
          AND o.razao_social NOT ILIKE '%DESCONHECIDA%'
        GROUP BY o.razao_social, o.uf
        HAVING SUM(p.win) >= 2 
        ORDER BY 3 DESC, 1 
        LIMIT 50
    """)
    consistency = db.execute(consistency_query).fetchall()
    
    return {
        "macro": {
            "total_despesas": total_geral,
            "media_por_operadora": media_geral,
            "total_operadoras_ativas": ativas,
            "tendencia_trimestral_percentual": tendencia
        },
        "top_movers": [
            {"razao_social": m.razao_social, "crescimento_percentual": m.cresc, "total_final": m.v_fim} 
            for m in movers
        ],
        "geo_eficiencia": [
            {"uf": g.uf, "total_despesas": g.total, "qtd_operadoras": g.qtd, "media_por_operadora": g.media} 
            for g in geo
        ],
        "consistencia": [
            {"razao_social": c.razao_social, "uf": c.uf, "qtd_trimestres_acima": c.qtd} 
            for c in consistency
        ]
    }

# ==============================================================================
# ROTA 4: Inteligência Artificial (Chat)
# ==============================================================================

# Schema interno para o request do chat
class ChatRequest(BaseModel):
    """
    Modelo de dados para recebimento de perguntas ao Chatbot.
    
    Atributos:
        question (str): A pergunta em linguagem natural do usuário.
    """
    question: str

@app.post("/api/ai/ask")
def ask_ai(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Processa uma pergunta em linguagem natural utilizando IA para consultar o banco de dados.
    
    Fluxo:
    1. Recebe a pergunta do usuário via 'request'.
    2. Utiliza o serviço 'process_user_query' para gerar e executar o SQL correspondente.
    3. Retorna os resultados da consulta ao banco.

    Argumentos:
        request (ChatRequest): Objeto contendo a pergunta.
        db (Session): Sessão do banco de dados.
        
    Retorna:
        dict: Resultado da consulta SQL gerada pela IA.
    """
    response = process_user_query(request.question, db)
    return response