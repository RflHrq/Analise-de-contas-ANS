from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Schema para Operadora Simples ---
class OperadoraSimples(BaseModel):
    """
    Representação simplificada de uma Operadora de Saúde.
    Utilizada para listagens e visualizações resumidas.
    """
    registro_ans: str
    cnpj: str
    razao_social: str
    modalidade: Optional[str]
    uf: Optional[str]

    class Config:
        from_attributes = True # Permite ler direto do SQLAlchemy

class DespesaDetalhe(BaseModel):
    """
    Detalhes de uma despesa ou evento contábil.
    Representa um registro individual de custo associado a um período.
    """
    ano: int
    trimestre: int
    conta_contabil: Optional[str]
    descricao: Optional[str]
    valor: float

    class Config:
        from_attributes = True

class EstatisticasGerais(BaseModel):
    """
    Estatísticas gerais do mercado de operadoras.
    Agrega dados de mercado, média e distribuição geográfica.
    """
    total_mercado: float
    media_por_operadora: float
    top_5_operadoras: List[dict]
    distribuicao_uf: List[dict]

# --- Schema de Paginação ---
class PaginatedOperadoras(BaseModel):
    """
    Modelo de resposta para listagem paginada de operadoras.
    Contém metadados da paginação e a lista de registros da página atual.
    """
    total: int
    page: int
    limit: int
    data: List[OperadoraSimples]

# 3. SCHEMAS DE INOVAÇÃO (Storytelling / Dashboard Avançado 'extra')

class KpiMacro(BaseModel):
    """
    Indicadores Chave de Desempenho (KPIs) macroeconômicos do dashboard.
    Fornece uma visão geral financeira e de atividade do setor.
    """
    total_despesas: float
    media_por_operadora: float
    total_operadoras_ativas: int
    tendencia_trimestral_percentual: float

class TopMover(BaseModel):
    """
    Representa uma operadora com movimentação expressiva (crescimento/queda).
    Utilizado para identificar destaques positivos ou negativos no período.
    """
    razao_social: str
    crescimento_percentual: float
    total_final: float

class GeoEficiencia(BaseModel):
    """
    Métricas de eficiência e volume agrupadas por localização (UF).
    Permite análise regional do mercado de saúde suplementar.
    """
    uf: str
    total_despesas: float
    qtd_operadoras: int
    media_por_operadora: float

class ConsistencyData(BaseModel):
    """
    Dados de consistência de desempenho de uma operadora.
    Indica a frequência com que a operadora supera a média do mercado.
    """
    razao_social: str
    uf: str
    qtd_trimestres_acima: int

class DashboardStorytelling(BaseModel):
    """
    Estrutura completa do Dashboard de Storytelling.
    Agrega todas as seções analíticas para apresentação no frontend.
    """
    macro: KpiMacro
    top_movers: List[TopMover]
    geo_eficiencia: List[GeoEficiencia]
    consistencia: List[ConsistencyData]