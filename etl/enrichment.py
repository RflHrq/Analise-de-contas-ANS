import pandas as pd
import os
import logging
import requests
import sys

# Importações locais
from config import (
    DATA_DIR, OUTPUT_FILE, ENRICHED_FILE,
    CADASTRO_URL, USER_AGENT, 
    CADOP_POSSIBLE_MAPPINGS
)

# Tenta importar o validador. Se não existir, cria um dummy para não quebrar.
try:
    from utils.validators import CNPJValidator
except ImportError:
    # Fallback seguro caso o arquivo utils não tenha sido criado ainda
    class CNPJValidator:
        @staticmethod
        def validate(cnpj): return True

class DataEnricher:
    """
    Classe responsável por enriquecer os dados financeiros (Fato) com 
    dados cadastrais (Dimensão) obtidos do portal da ANS.
    """
    
    CADASTRO_FILE = os.path.join(DATA_DIR, "cadastro_operadoras.csv")

    def __init__(self):
        self.logger = logging.getLogger("ANS_ETL.Enricher")
        self.enriched_file = ENRICHED_FILE

    def download_cadastro(self):
        """
        Baixa o CSV de Operadoras Ativas (CADOP) se ele ainda não existir.
        """
        if os.path.exists(self.CADASTRO_FILE):
            self.logger.info("Arquivo de cadastro já existe localmente.")
            return

        self.logger.info("Baixando cadastro oficial da ANS (CADOP)...")
        try:
            headers = {'User-Agent': USER_AGENT}
            # verify=False é necessário pois o cert da ANS frequentemente expira ou é autoassinado
            with requests.get(CADASTRO_URL, headers=headers, stream=True, verify=False, timeout=60) as r:
                r.raise_for_status()
                with open(self.CADASTRO_FILE, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            self.logger.info("Download concluído com sucesso.")
        except Exception as e:
            self.logger.error(f"Erro crítico no download do cadastro: {e}")
            raise

    def load_cadop_robust(self):
        """
        Lê o arquivo CADOP lidando com diferentes encodings e separadores.
        Retorna: 
            DataFrame: Dados cadastrais limpos e normalizados.
        """
        # 1. Tentativa de Leitura (Encoding Windows vs UTF8)
        try:
            df = pd.read_csv(self.CADASTRO_FILE, sep=';', encoding='cp1252', dtype=str, on_bad_lines='skip')
        except:
            df = pd.read_csv(self.CADASTRO_FILE, sep=';', encoding='utf-8', dtype=str, on_bad_lines='skip')

        # 2. Normalização de Colunas (Upper Case + Strip)
        df.columns = [c.strip().upper() for c in df.columns]

        # 3. Mapeamento Inteligente (De -> Para)
        # Usa o dicionário do config.py para encontrar as colunas certas independente do nome
        final_rename_map = {}
        for target, candidates in CADOP_POSSIBLE_MAPPINGS.items():
            found = False
            for source in candidates:
                if source in df.columns:
                    final_rename_map[source] = target
                    found = True
                    break
            
            if not found and target == 'RegistroANS':
                raise ValueError(f"Coluna RegistroANS não encontrada no CADOP. Colunas disponíveis: {df.columns}")

        df.rename(columns=final_rename_map, inplace=True)

        # 4. Seleção e Limpeza
        # Garante que temos apenas as colunas mapeadas que existem no DF
        cols_to_keep = [col for col in [
            'RegistroANS', 'CNPJ_Cad', 'RazaoSocial_Cad', 'UF', 'Modalidade',
            'Nome_Fantasia', 'Logradouro', 'Numero', 'Complemento', 'Bairro', 'Cidade', 'CEP',
            'DDD', 'Telefone', 'Fax', 'Endereco_eletronico', 'Representante', 'Cargo_Representante',
            'Regiao_de_Comercializacao', 'Data_Registro_ANS'
        ] if col in df.columns]
        df = df[cols_to_keep].copy()

        # Limpeza da Chave Primária
        df['RegistroANS'] = df['RegistroANS'].str.strip().str.replace('"', '').str.replace("'", "")
        
        # Remove duplicatas (Pega o primeiro registro ativo encontrado)
        df.drop_duplicates(subset=['RegistroANS'], inplace=True)
        
        return df

    def process(self):
        """
        Executa o enriquecimento de dados:
        1. Carrega dados financeiros consolidados.
        2. Baixa e carrega dados cadastrais (CADOP).
        3. Cruza informações (Join) pelo RegistroANS.
        4. Valida CNPJs.
        5. Salva arquivo final enriquecido.
        """
        self.logger.info("Iniciando Enriquecimento de Dados...")
        
        # --- PASSO 1: Carregar Dados Financeiros ---
        if not os.path.exists(OUTPUT_FILE):
            self.logger.error("Arquivo consolidado (consolidado_despesas.csv) não encontrado.")
            return

        try:
            # Tenta abrir (se estiver aberto no Excel, vai dar erro aqui)
            with open(OUTPUT_FILE, 'r'): pass 
            
            df_despesas = pd.read_csv(OUTPUT_FILE, sep=';', encoding='utf-8-sig', dtype=str)
        except PermissionError:
            self.logger.critical(f"ERRO DE PERMISSÃO: O arquivo '{OUTPUT_FILE}' está aberto. Feche-o e tente novamente.")
            return

        # Remove colunas vazias/placeholders para evitar colisão no merge
        cols_to_drop = [c for c in ['Modalidade', 'UF'] if c in df_despesas.columns]
        if cols_to_drop:
            df_despesas.drop(columns=cols_to_drop, inplace=True)

        # Limpeza da Chave Primária (Financeiro)
        df_despesas['RegistroANS'] = df_despesas['RegistroANS'].str.strip().str.replace('"', '').str.replace("'", "")

        # --- PASSO 2: Carregar Dados Cadastrais ---
        self.download_cadastro()
        self.logger.info("Processando arquivo de cadastro...")
        df_ops = self.load_cadop_robust()

        # --- PASSO 3: Executar o Join (Left Join) ---
        self.logger.info("Cruzando dados financeiros com cadastrais...")
        
        # Left Join: Mantém todas as despesas, traz dados da operadora se existir
        df_merged = pd.merge(df_despesas, df_ops, on='RegistroANS', how='left')

        # --- PASSO 4: Consolidar Colunas ---
        # Se CNPJ do cadastro existe, usa ele. Se não, mantém o que tinha (se houver).
        if 'CNPJ_Cad' in df_merged.columns:
            df_merged['CNPJ'] = df_merged['CNPJ_Cad'].fillna(df_merged['CNPJ'] if 'CNPJ' in df_merged else "")
        
        if 'RazaoSocial_Cad' in df_merged.columns:
            df_merged['RazaoSocial'] = df_merged['RazaoSocial_Cad'].fillna(df_merged['RazaoSocial'] if 'RazaoSocial' in df_merged else "")

        # Limpa colunas temporárias do Join
        df_merged.drop(columns=['CNPJ_Cad', 'RazaoSocial_Cad'], inplace=True, errors='ignore')

        # --- PASSO 5: Tratamento de Falhas (Dados Faltantes) ---
        # Operadoras que não deram match no cadastro (provavelmente canceladas)
        df_merged['RazaoSocial'] = df_merged['RazaoSocial'].fillna("OPERADORA INATIVA/DESCONHECIDA")
        
        # Se Modalidade não veio do Join, marca como Desconhecida
        if 'Modalidade' not in df_merged.columns:
            df_merged['Modalidade'] = 'Desconhecida'
        else:
            df_merged['Modalidade'] = df_merged['Modalidade'].fillna('Desconhecida')

        if 'UF' not in df_merged.columns:
            df_merged['UF'] = 'ND'
        else:
            df_merged['UF'] = df_merged['UF'].fillna('ND')

        # --- PASSO 6: Validação de Qualidade (CNPJ) ---
        self.logger.info("Executando validação algorítmica de CNPJs...")
        
        # Aplica o validador
        df_merged['CNPJ_Valido'] = df_merged['CNPJ'].apply(lambda x: CNPJValidator.validate(x))
        
        # Estatísticas de Qualidade
        total = len(df_merged)
        invalidos = len(df_merged[~df_merged['CNPJ_Valido']])
        self.logger.info(f"Qualidade dos Dados: {invalidos} registros com CNPJ inválido ou ausente de {total} ({invalidos/total:.1%}).")

        # --- PASSO 7: Salvar Resultado ---
        self.logger.info(f"Salvando arquivo final: {self.enriched_file}")
        
        try:
            df_merged.to_csv(self.enriched_file, index=False, sep=';', encoding='utf-8-sig')
            self.logger.info("Enriquecimento concluído com sucesso!")
        except PermissionError:
            self.logger.critical("ERRO DE PERMISSÃO: O arquivo 'despesas_enriquecidas.csv' está aberto no Excel.")
            self.logger.critical("   -> FECHE O ARQUIVO e rode novamente.")
        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivo: {e}")
            raise