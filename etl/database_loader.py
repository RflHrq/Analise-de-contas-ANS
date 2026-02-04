import pandas as pd
import logging
import os
from sqlalchemy import create_engine, text
from config import ENRICHED_FILE, AGGREGATED_FILE, BASE_DIR, DATABASE_URL

class DatabaseLoader:
    """
    Gerencia a carga de dados (Loading) para o banco de dados PostgreSQL.
    Configura tabelas via DDL e insere dados processados.
    """
    def __init__(self):
        self.logger = logging.getLogger("ANS_ETL.Loader")
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        try:
            self.engine = create_engine(DATABASE_URL, echo=False)
            self.logger.info(f"Conectado ao banco: {DATABASE_URL.split('@')[-1]}")
        except Exception as e:
            self.logger.critical(f"Erro ao configurar engine do banco: {e}")
            raise

    def init_db(self):
        """
        Executa o script DDL (Data Definition Language) para criar as tabelas.
        Lê o arquivo schema.sql e executa os comandos SQL.
        """
        schema_path = os.path.join(BASE_DIR, "database", "schema.sql")
        self.logger.info("Inicializando estrutura do banco de dados (DDL)...")
        if not os.path.exists(schema_path):
             self.logger.error(f"Schema não encontrado: {schema_path}")
             return

        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        try:
            # AUTOCOMMIT resolve problemas de transação abortada em comandos DDL/Role
            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                for statement in sql_script.split(';'):
                    if statement.strip():
                        try:
                            conn.execute(text(statement))
                        except Exception as e:
                            err_msg = str(e).lower()
                            # Ignora erros de "já existe" (CREATE) ou "não existe" (DROP)
                            if "already exists" in err_msg or "duplicateobject" in err_msg:
                                self.logger.warning(f"⚠️  Objeto já existe, ignorando: {statement.splitlines()[0][:50]}...")
                            elif ("does not exist" in err_msg or "undefinedobject" in err_msg) and "DROP" in statement.upper():
                                self.logger.warning(f"⚠️  Objeto não existe para dropar, ignorando: {statement.splitlines()[0][:50]}...")
                            else:
                                self.logger.error(f"❌ Erro SQL: {err_msg}")
                                # Não relança erro fatal para permitir que o script tente continuar (Best Effort)
                                # Mas se falhar algo crítico, o resto pode quebrar depois. 
                                # Para CREATE ROLE, é seguro seguir.
                                pass
            self.logger.info("Tabelas criadas/verificadas com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro ao executar DDL: {e}")
            raise

    # --- FUNÇÃO NOVA: PADRONIZAÇÃO DE ID ---
    def _standardize_id(self, series):
        """
        Garante que o Registro ANS seja sempre uma string limpa, sem zeros à esquerda
        e sem '.0' decimal, para garantir o match entre tabelas.
        Ex: '005711' vira '5711', '5711.0' vira '5711'.
        """
        # 1. Remove ponto flutuante (.0) se houver
        clean = series.astype(str).str.replace(r'\.0$', '', regex=True)
        # 2. Converte para inteiro e volta para string (remove zeros à esquerda: "005711" -> "5711")
        #    Usamos pd.to_numeric com errors='coerce' para evitar quebra em lixo
        return pd.to_numeric(clean, errors='coerce').fillna(0).astype(int).astype(str)

    def process(self):
        """
        Orquestra o pipeline de carga:
        1. Lê o arquivo CSV final (Enriquecido).
        2. Padroniza IDs (RegistroANS).
        3. Carrega Operadoras (Dimensão).
        4. Carrega Despesas (Fato).
        5. Calcula e Carrega Agregados (ELT).
        """
        self.logger.info("Iniciando Pipeline de Carga (ETL -> SQL)...")

        if not os.path.exists(ENRICHED_FILE):
            self.logger.error("Arquivo enriquecido não encontrado.")
            return

        try:
            self.logger.info("Lendo arquivo enriquecido...")
            df = pd.read_csv(ENRICHED_FILE, sep=';', encoding='utf-8-sig', dtype=str)
            
            # --- PADRONIZAÇÃO CRÍTICA DO ID ---
            df['RegistroANS'] = self._standardize_id(df['RegistroANS'])
            
            # Tratamento de Tipos
            df['Valor Despesas'] = df['Valor Despesas'].str.replace(',', '.', regex=False)
            df['Valor Despesas'] = pd.to_numeric(df['Valor Despesas'], errors='coerce').fillna(0)
            df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce')
            df['Trimestre'] = pd.to_numeric(df['Trimestre'], errors='coerce')

            self._load_operadoras(df)
            self._load_despesas(df)
            self._load_agregadas()

            self.logger.info("✅ Pipeline de Banco de Dados finalizado com sucesso!")

        except Exception as e:
            self.logger.critical(f"Falha fatal durante a carga no banco: {e}")

    def _load_operadoras(self, df):
        self.logger.info("Carregando tabela: OPERADORAS...")
        cols_ops = [
            'RegistroANS', 'CNPJ', 'RazaoSocial', 'Modalidade', 'UF',
            'Nome_Fantasia', 'Logradouro', 'Numero', 'Complemento', 'Bairro', 'Cidade', 'CEP',
            'DDD', 'Telefone', 'Fax', 'Endereco_eletronico', 'Representante', 'Cargo_Representante',
            'Regiao_de_Comercializacao', 'Data_Registro_ANS'
        ]
        # Garante que as colunas existem (caso o enriquecimento tenha falhado parcialmente)
        for col in cols_ops:
            if col not in df.columns:
                df[col] = None

        df_ops = df[cols_ops].drop_duplicates(subset=['RegistroANS']).copy()
        
        # Tratamento de CNPJ nulo
        df_ops['CNPJ'] = df_ops['CNPJ'].fillna('00.000.000/0000-00')
        df_ops.loc[df_ops['CNPJ'].str.strip() == '', 'CNPJ'] = '00.000.000/0000-00'
        
        rename_ops = {
            'RegistroANS': 'registro_ans', 'CNPJ': 'cnpj', 
            'RazaoSocial': 'razao_social', 'Modalidade': 'modalidade', 'UF': 'uf',
            'Nome_Fantasia': 'nome_fantasia', 'Logradouro': 'logradouro', 'Numero': 'numero',
            'Complemento': 'complemento', 'Bairro': 'bairro', 'Cidade': 'cidade', 'CEP': 'cep',
            'DDD': 'ddd', 'Telefone': 'telefone', 'Fax': 'fax', 'Endereco_eletronico': 'endereco_eletronico',
            'Representante': 'representante', 'Cargo_Representante': 'cargo_representante',
            'Regiao_de_Comercializacao': 'regiao_comercializacao', 'Data_Registro_ANS': 'data_registro_ans'
        }
        df_ops.rename(columns=rename_ops, inplace=True)
        df_ops.to_sql('operadoras', self.engine, if_exists='append', index=False, method='multi', chunksize=1000)

    def _load_despesas(self, df):
        self.logger.info("Carregando tabela: DESPESAS_EVENTOS...")
        cols_fact = ['RegistroANS', 'Ano', 'Trimestre', 'Conta', 'Descricao', 'Valor Despesas']
        df_fact = df[cols_fact].copy()
        
        rename_fact = {
            'RegistroANS': 'registro_ans', 'Ano': 'ano', 'Trimestre': 'trimestre',
            'Conta': 'conta_contabil', 'Descricao': 'descricao', 
            'Valor Despesas': 'valor'
        }
        df_fact.rename(columns=rename_fact, inplace=True)
        df_fact.to_sql('despesas_eventos', self.engine, if_exists='append', index=False, method='multi', chunksize=5000)

    def _load_agregadas(self):
        self.logger.info("Carregando tabela: DESPESAS_AGREGADAS (Via SQL)...")
        
        # ELT: Transformação dentro do banco para máxima performance
        query_elt = text("""
            TRUNCATE TABLE despesas_agregadas;
            
            INSERT INTO despesas_agregadas (registro_ans, total_despesas, media_trimestral, desvio_padrao, qtde_trimestres, data_processamento)
            WITH trimestral AS (
                SELECT registro_ans, ano, trimestre, SUM(valor) as total
                FROM despesas_eventos
                GROUP BY registro_ans, ano, trimestre
            )
            SELECT 
                registro_ans,
                COALESCE(SUM(total), 0),
                COALESCE(AVG(total), 0),
                COALESCE(STDDEV(total), 0),
                COUNT(*),
                NOW()
            FROM trimestral
            GROUP BY registro_ans;
        """)

        try:
            with self.engine.connect() as conn:
                conn.execute(query_elt)
                conn.commit()
            self.logger.info("✅ Tabela Agregada calculada com sucesso via SQL.")
        except Exception as e:
            self.logger.error(f"Erro ao calcular agregados via SQL: {e}")
            raise 