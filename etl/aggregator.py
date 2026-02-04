import pandas as pd
import numpy as np
import os
import logging
from utils.compression import FileCompressor 
from config import ENRICHED_FILE, AGGREGATED_FILE, PROCESSED_DIR

class DataAggregator:
    """
    Classe responsável por agregar dados financeiros para gerar estatísticas.
    Calcula totais trimestrais e métricas estatísticas (média, desvio padrão).
    """
    def __init__(self):
        self.logger = logging.getLogger("ANS_ETL.Aggregator")
        self.input_file = ENRICHED_FILE
        self.output_file = AGGREGATED_FILE

    def process(self):
        """
        Executa o fluxo de agregação:
        1. Lê o arquivo enriquecido.
        2. Calcula totais por trimestre.
        3. Gera estatísticas gerais (Média, Desvio Padrão).
        4. Salva o resultado agregado.
        """
        self.logger.info("Iniciando Agregação Estatística...")

        if not os.path.exists(self.input_file):
            self.logger.error("Arquivo enriquecido não encontrado.")
            return

        try:
            cols_needed = ['RegistroANS', 'RazaoSocial', 'UF', 'Modalidade', 'Ano', 'Trimestre', 'Valor Despesas']
            df = pd.read_csv(self.input_file, sep=';', encoding='utf-8-sig', usecols=cols_needed)
            
            df['Valor Despesas'] = pd.to_numeric(df['Valor Despesas'], errors='coerce').fillna(0)

            # 1. Totais Trimestrais
            self.logger.info("Calculando totais trimestrais...")
            df_trimestral = df.groupby(
                ['RegistroANS', 'RazaoSocial', 'UF', 'Modalidade', 'Ano', 'Trimestre']
            )['Valor Despesas'].sum().reset_index()
            
            df_trimestral.rename(columns={'Valor Despesas': 'Despesa_Trimestral'}, inplace=True)

            # 2. Estatísticas Gerais
            self.logger.info("Calculando estatísticas finais...")
            stats = df_trimestral.groupby(['RegistroANS', 'RazaoSocial', 'UF', 'Modalidade'])['Despesa_Trimestral'].agg(
                Total_Despesas='sum',
                Media_Trimestral='mean',
                Desvio_Padrao='std',
                Qtde_Trimestres='count'
            ).reset_index()

            stats['Desvio_Padrao'] = stats['Desvio_Padrao'].fillna(0)
            
            # Ordenação
            stats.sort_values(by='Total_Despesas', ascending=False, inplace=True)
            stats['Total_Despesas'] = stats['Total_Despesas'].round(2)
            stats['Media_Trimestral'] = stats['Media_Trimestral'].round(2)
            stats['Desvio_Padrao'] = stats['Desvio_Padrao'].round(2)

            self.logger.info(f"Salvando CSV agregado: {self.output_file}")
            stats.to_csv(self.output_file, index=False, sep=';', encoding='utf-8-sig')
            
            self.logger.info("Estatísticas geradas com sucesso.")

            # Compacta o arquivo resultante
            self.logger.info("Iniciando compactação do arquivo agregado...")
            zip_name = "Teste_Rafael_Henrique_dos_Santos_Simao.zip"
            dest_zip = os.path.join(PROCESSED_DIR, zip_name)
            FileCompressor.compress(self.output_file, dest_zip)

        except Exception as e:
            self.logger.critical(f"Erro fatal na agregação: {e}")
            raise