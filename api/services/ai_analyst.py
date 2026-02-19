import os
from groq import Groq
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# ==============================================================================
#  CHAVE CARREGADA DO .ENV
# ==============================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Log de DEBUG (seguro, mostra apenas os 4 primeiros caracteres)
print(f"🔍 DEBUG: Iniciando serviço de IA. Chave configurada: {GROQ_API_KEY[:4]}..." if GROQ_API_KEY else "❌ ERRO: Chave não encontrada!")

try:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY não encontrada no arquivo .env")
        
    client = Groq(api_key=GROQ_API_KEY)
    print("DEBUG: Cliente Groq inicializado com sucesso.")
except Exception as e:
    print(f"DEBUG: Erro ao iniciar cliente Groq: {e}")

# ==============================================================================
# O CÉREBRO DA IA: DEFINIÇÃO DE ESQUEMA E ENGENHARIA DE PROMPT
# ==============================================================================
DB_SCHEMA = """
Você é um especialista em SQL PostgreSQL, com profundo conhecimento em modelagem dimensional (Star Schema) e nos dados da ANS (Agência Nacional de Saúde Suplementar).

Você recebe perguntas em linguagem natural e deve convertê-las em UMA QUERY SQL PostgreSQL VÁLIDA, precisa e eficiente.

ESQUEMA DO BANCO DE DADOS (IMUTÁVEL)
DIMENSÃO: operadoras
Representa os dados cadastrais das operadoras.
<operadoras>
- registro_ans (PK, varchar): Identificador único da operadora
- cnpj (varchar)
- razao_social (varchar): Nome da operadora
- nome_fantasia (varchar)
- modalidade (varchar)
- logradouro (varchar)
- numero (varchar)
- complemento (varchar)
- bairro (varchar)
- cidade (varchar)
- uf (varchar): Sigla do estado
- cep (varchar)
- ddd (varchar)
- telefone (varchar)
- fax (varchar)
- endereco_eletronico (varchar): E-mail da operadora
- representante (varchar): Nome do representante legal
- cargo_representante (varchar)
- regiao_comercializacao (varchar)
- data_registro_ans (varchar)
- data_atualizacao (timestamp)
</operadoras>

FATO TRANSACIONAL: despesas_eventos
Guarda lançamentos contábeis detalhados.
<despesas_eventos>
id (PK)
registro_ans (FK → operadoras.registro_ans)
ano (int)
trimestre (int)
conta_contabil (varchar)
descricao (varchar)
valor (numeric)
</despesas_eventos>

FATO ANALÍTICO: despesas_agregadas
Guarda KPIs já calculados.
<despesas_agregadas>
id (PK)
registro_ans (FK → operadoras.registro_ans)
total_despesas (numeric)
media_trimestral (numeric)
desvio_padrao (numeric)
qtde_trimestres (int)
data_processamento (timestamp)
</despesas_agregadas>

RELACIONAMENTOS (OBRIGATÓRIO)
Sempre use JOIN operadoras o ON <tabela_fato>.registro_ans = o.registro_ans quando:
A pergunta envolver nome da operadora, estado (uf), modalidade ou comparações entre operadoras.

SUA TAREFA
Converter a pergunta do usuário em SQL PostgreSQL, seguindo rigorosamente as regras abaixo.

REGRAS CRÍTICAS (NÃO QUEBRE)
Retorne APENAS o SQL
Sem explicações
Sem comentários
Sem markdown

NUNCA use: DELETE, UPDATE, INSERT, DROP, TRUNCATE

Para buscas textuais em nomes (Razão Social), use sempre: ILIKE '%TRECHO%DO%NOME%'
(DICA: Substitua espaços por % para lidar com variações de espaçamento ou palavras abreviadas)

Se a pergunta for sobre telefone ou contato, retorne SEMPRE: ddd, telefone (Ex: SELECT ddd, telefone FROM operadoras...)

Para valores financeiros detalhados, use: COALESCE(SUM(d.valor), 0) (Tabela: despesas_eventos)
Para KPIs prontos, use: Tabela: despesas_agregadas (Não recalcular métricas já existentes)

Quando a pergunta envolver:
“quem gastou mais” → ORDER BY SUM(valor) DESC
ranking → ORDER BY + LIMIT
tempo → usar ano e trimestre

Campos inexistentes NÃO DEVEM SER INVENTADOS
Não existe categoria
Use descricao ou conta_contabil

Use aliases curtos e claros:
o para operadoras
d para despesas_eventos
a para despesas_agregadas

BOAS PRÁTICAS
Prefira despesas_agregadas quando a pergunta for estratégica ou resumida
Prefira despesas_eventos quando for analítica ou detalhada
Agrupe corretamente usando GROUP BY
Retorne apenas as colunas necessárias.

Se o usuário pedir "quais são os campos", "tabelas" ou "estrutura do banco":
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

DEFINIÇÃO DE "MAIOR CRESCIMENTO" (Use SEMPRE esta lógica de CTEs):
WITH limites AS (
    SELECT MIN(ano*10+trimestre) as min_p, MAX(ano*10+trimestre) as max_p FROM despesas_eventos
),
inicio AS (
    SELECT d.registro_ans, SUM(d.valor) as total_ini 
    FROM despesas_eventos d, limites l 
    WHERE (d.ano*10+d.trimestre) = l.min_p 
    GROUP BY d.registro_ans
),
fim AS (
    SELECT d.registro_ans, SUM(d.valor) as total_fim 
    FROM despesas_eventos d, limites l 
    WHERE (d.ano*10+d.trimestre) = l.max_p 
    GROUP BY d.registro_ans
)
SELECT o.razao_social, i.total_ini, f.total_fim, ROUND(((f.total_fim - i.total_ini)/i.total_ini)*100, 2) as crescimento_pct
FROM operadoras o 
JOIN inicio i ON o.registro_ans = i.registro_ans 
JOIN fim f ON o.registro_ans = f.registro_ans
WHERE i.total_ini > 0 
ORDER BY 4 DESC 
LIMIT 5;

DEFINIÇÕES DE NEGÓCIO (IMPORTANTISSIMO):
- "Ticket Médio" ou "Média por Operadora" (especialmente por Estado/UF) no Dashboard é calculado como: O TOTAL DE DESPESAS ACUMULADO dividido pela QUANTIDADE DE OPERADORAS.
- Fórmula SQL para Ticket Médio por UF: SUM(a.total_despesas) / COUNT(a.registro_ans) (Usando tabela 'despesas_agregadas').
- NUNCA use AVG(media_trimestral) para responder "Ticket Médio por Estado", pois isso dará a média de um único trimestre, e o dashboard mostra o acumulado.

- TRATAMENTO DE NULOS (CRÍTICO):
Se o usuário perguntar por um dado específico (ex: "Qual o telefone", "Qual o email", "Qual o fax"), adicione SEMPRE: WHERE campo IS NOT NULL AND campo != '' para não retornar linhas vazias.
     
INTERPRETAÇÃO DE TERMOS E GÍRIAS:
- "TUDO", "ISSO", "TOTAL", "QUANTO GASTOU": Entenda como "Total de Despesas Consolidado" (SUM(valor)) da operadora em todos os períodos disponíveis.
- "CORE": Entenda como atividade principal.
- "SINISTRO": Entenda como "Eventos Avisados" (Conta iniciada em 4.1.1).

FILTRO DE RELEVÂNCIA (NOVA REGRA CRÍTICA):
Analise se a pergunta tem relação com o banco de dados (Operadoras, Despesas, CNPJ, Estados, Finanças, Saúde).
Se a pergunta for "Oi", "Tudo bem", "Como vai", ou random words/nonsense que não se aplicam ao contexto de dados("qual o sentido da vida", "receita de bolo"):
RETORNE APENAS A STRING: INVALID_QUERY
"""

def process_user_query(user_question: str, db: Session):
    """
    Processa a pergunta do usuário:
    1. Gera SQL via LLM (Groq/Llama 3).
    2. Blinda contra SQL Injection.
    3. Executa no banco de dados.
    4. Trata retornos vazios ou nulos.
    """
    print(f"\nDEBUG: Recebi pergunta do usuário: '{user_question}'")
    
    try:
        # 1. ENGENHARIA DE PROMPT (Text-to-SQL)
        print("DEBUG: Montando prompt...")
        system_prompt = f"""
        {DB_SCHEMA}
        
        PERGUNTA DO USUÁRIO: "{user_question}"
        """

        # 2. Chamada Groq (Geração da Query)
        print("DEBUG: Enviando para a Groq (Llama 3.3)...")
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0, 
            max_tokens=500
        )
        
        generated_sql = chat_completion.choices[0].message.content.strip()

        # [VALIDAÇÃO] Filtro de perguntas irrelevantes (Delírios)
        if generated_sql == "INVALID_QUERY":
            return {
                "error": "Desculpe, só consigo responder perguntas sobre dados financeiros das Operadoras de Saúde (ANS)."
            }
    
        # Limpeza Básica do SQL
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
        if generated_sql.endswith(";"): 
            generated_sql = generated_sql[:-1]

        print(f"DEBUG: SQL Limpo: {generated_sql}")

        # ==============================================================================
        # BLINDAGEM ANTI-INJECTION
        # ==============================================================================
        
        sql_upper = generated_sql.upper()

        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            print("DEBUG: Bloqueado. Query não começa com SELECT/WITH.")
            return {"error": "Por segurança, apenas consultas de leitura são permitidas."}

        if ";" in generated_sql:
            print("DEBUG: Bloqueado. Tentativa de injeção de múltiplas queries (;).")
            return {"error": "Consulta inválida detectada."}

        forbidden = [
            "DROP ", "DELETE ", "UPDATE ", "INSERT ", "TRUNCATE ", "ALTER ", 
            "GRANT ", "REVOKE ", "CREATE ", "EXEC ", "EXECUTE ", "Pg_"
        ]
        if any(cmd in sql_upper for cmd in forbidden):
            print(f"DEBUG: Bloqueado por conter palavra proibida.")
            return {"error": "Comando não permitido detectado."}

        # ==============================================================================
        # FIM DA BLINDAGEM
        # ==============================================================================

        # 3. Execução no Banco de Dados
        print(f"DEBUG: Executando no Banco...")

        result = db.execute(text(generated_sql))
        columns = result.keys()
        data = [dict(zip(columns, row)) for row in result.fetchall()]
        
        print(f"DEBUG: Sucesso! {len(data)} linhas encontradas.")

        # [VALIDAÇÃO] Sem resultados encontrados
        if len(data) == 0:
            return {
                "sql": generated_sql,
                "data": [],
                "count": 0,
                "error": "Não encontrei nenhum registro no banco que corresponda à sua pesquisa."
            }

        # [VALIDAÇÃO] Resultados encontrados mas vazios (ex: Fax Nulo)
        has_content = False
        for row in data:
            for value in row.values():
                if value is not None and str(value).strip() != "":
                    has_content = True
                    break
            if has_content:
                break
        
        if not has_content:
             # Tentativa de identificar o contexto pela coluna
             cols = [c.lower() for c in columns]
             if any(term in cols for term in ['total', 'valor', 'soma', 'despesa', 'gasto']):
                 return {
                    "sql": generated_sql,
                    "data": [{"resultado": "R$ 0,00"}],
                    "count": 1,
                    "error": None # Não é erro, é zero.
                 }
             
             return {
                "sql": generated_sql,
                "data": [],
                "count": 0,
                "error": "Encontrei o registro, mas a informação solicitada não consta na base de dados (valor nulo ou vazio)."
            }
        
        return {
            "sql": generated_sql,
            "data": data,
            "count": len(data)
        }

    except Exception as e:
        print(f"ERRO CRÍTICO NO BACKEND: {str(e)}")
        return {"error": f"Erro interno no servidor: {str(e)}"}