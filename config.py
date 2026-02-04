import os

# --- 1. INFRAESTRUTURA DE DIRETÓRIOS ---
BASE_DIR = os.getcwd()
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")          
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUTPUT_FILE = os.path.join(DATA_DIR, "consolidado_despesas.csv")
ENRICHED_FILE = os.path.join(DATA_DIR, "despesas_enriquecidas.csv")
AGGREGATED_FILE = os.path.join(DATA_DIR, "despesas_agregadas.csv")

# --- 2. CONFIGURAÇÕES DE REDE E URLS ---
ANS_BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
CADASTRO_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

HTTP_TIMEOUT = 60
MAX_RETRIES = 3
BACKOFF_FACTOR = 1
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
HEADERS = {'User-Agent': USER_AGENT}

# --- 3. CONFIGURAÇÕES DE ETL (GERAL) ---
CHUNK_SIZE = 50000 
FINAL_COLUMNS = ["RegistroANS", "CNPJ", "RazaoSocial", "Trimestre", "Ano", "Conta", "Descricao", "Modalidade", "Valor Despesas"]

# Mapeamento para normalizar nomes de colunas do CSV Financeiro
COLUMN_MAPPING = {
    "REG_ANS": "RegistroANS",
    "CD_CONTA_CONTABIL": "Conta",
    "DESCRICAO": "Descricao",
    "VL_SALDO_FINAL": "Valor Despesas",
    "NR_CNPJ": "CNPJ",
    "NO_RAZAO_SOCIAL": "RazaoSocial",
}


# Conta 4 (Despesas Assistenciais) e 2 (Passivo - para validações se necessário)
# Filtramos apenas as despesas operacionais (Grupo 4) que nos interessam
ACCOUNT_PREFIX_FILTER = ["41"]
 

# --- 5. REGRAS DE ENRIQUECIMENTO (CADASTRO) ---
# Mapeamento flexível para colunas do CADOP (Resiliência a mudanças da ANS)
CADOP_POSSIBLE_MAPPINGS = {
    'RegistroANS': ['REGISTRO_OPERADORA', 'REGISTRO_ANS', 'REG_ANS', 'CD_OPERADORA'],
    'CNPJ_Cad': ['CNPJ', 'NR_CNPJ'],
    'RazaoSocial_Cad': ['RAZAO_SOCIAL', 'NM_RAZAO_SOCIAL', 'NOM_OPERADORA', 'NO_RAZAO_SOCIAL'],
    'UF': ['UF', 'SG_UF', 'CD_UF'],
    'Modalidade': ['MODALIDADE', 'DS_MODALIDADE', 'DESCRICAO_MODALIDADE', 'TIPO_OPERADORA'],
    'Nome_Fantasia': ['NOME_FANTASIA', 'NO_FANTASIA'],
    'Logradouro': ['LOGRADOURO', 'DE_LOGRADOURO'],
    'Numero': ['NUMERO', 'NU_ENDERECO'],
    'Complemento': ['COMPLEMENTO', 'DE_COMPLEMENTO'],
    'Bairro': ['BAIRRO', 'NO_BAIRRO'],
    'Cidade': ['CIDADE', 'NO_CIDADE', 'MUNICIPIO'],
    'CEP': ['CEP', 'CO_CEP'],
    'DDD': ['DDD', 'NU_DDD'],
    'Telefone': ['TELEFONE', 'NU_TELEFONE'],
    'Fax': ['FAX', 'NU_FAX'],
    'Endereco_eletronico': ['ENDERECO_ELETRONICO', 'EMAIL', 'NO_EMAIL'],
    'Representante': ['REPRESENTANTE', 'NO_REPRESENTANTE'],
    'Cargo_Representante': ['CARGO_REPRESENTANTE', 'DS_CARGO_REPRESENTANTE'],
    'Regiao_de_Comercializacao': ['REGIAO_DE_COMERCIALIZACAO', 'DS_REGIAO'],
    'Data_Registro_ANS': ['DATA_REGISTRO_ANS', 'DT_REGISTRO']
}

# --- 6. CONFIGURAÇÃO DE BANCO DE DADOS ---
# --- 6. CONFIGURAÇÃO DE BANCO DE DADOS ---
# Ajuste aqui suas credenciais locais
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ans_db")

# URL de Escrita (ETL)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configuração do Usuário Leitor (Para a API)
# Tenta carregar do .env primeiro (DATABASE_URL), senão monta manual (Fallback inseguro removido)
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL_READER = os.getenv("DATABASE_URL")

if not DATABASE_URL_READER:
    # Fallback apenas para não quebrar em dev local se .env falhar, mas avisando
    print("⚠️ AVISO: DATABASE_URL não encontrada no .env. Usando configuração padrão (pode falhar se senha estiver errada).")
    # Tenta usar a mesma de escrita como fallback temporário
    DATABASE_URL_READER = DATABASE_URL