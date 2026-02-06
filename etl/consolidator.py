import os
import pandas as pd
import logging
import csv
from utils.compression import FileCompressor
from config import (
    PROCESSED_DIR, OUTPUT_FILE, COLUMN_MAPPING, 
    CHUNK_SIZE, FINAL_COLUMNS, 
    ACCOUNT_PREFIX_FILTER
)

class DataConsolidator:
    """
    Consolida múltiplos arquivos CSV/TXT brutos em um único arquivo padronizado.
    Realiza normalização de colunas, detecção de encoding e filtragem de contas contábeis.
    """
    def __init__(self):
        self.logger = logging.getLogger("ANS_ETL.Consolidator")
        self.output_file = OUTPUT_FILE
    
    def _identify_separator(self, filepath, encoding):
        try:
            with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                sample = f.read(4096)
                if ';' in sample and sample.count(';') > sample.count(','): return ';'
                sniffer = csv.Sniffer()
                return sniffer.sniff(sample, delimiters=';,\t').delimiter
        except: return ';'
    
    def _detect_encoding(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read(8192)
            return 'utf-8'
        except UnicodeDecodeError:
            return 'cp1252'

    def _is_valid_file(self, filename):
        return filename.lower().endswith(('.csv', '.txt'))

    def _extract_date_info(self, filepath):
        path_parts = filepath.split(os.sep)
        for part in path_parts:
            if 'T' in part and len(part) == 6 and part[0].isdigit():
                return part[0], part[2:]
        return None, None






    def process(self):
        """
        Executa a consolidação dos arquivos:
        1. Varre o diretório de processados.
        2. Detecta metadados (Trimestre, Ano, Separador, Encoding).
        3. Lê em chunks para otimização de memória.
        4. Normaliza colunas e valores numéricos.
        5. Salva incrementalmente no arquivo de saída.
        """
        self.logger.info("Iniciando consolidação...")
        
        # Robust Delete (Fix para Windows)
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
                import time
                time.sleep(0.5)
            except OSError:
                pass
        
        header_written = False
        files_processed = 0

        # [OTIMIZAÇÃO] Abre o arquivo UMA VEZ e mantém aberto.
        # Isso evita Race Conditions de File Lock no Windows e acelera o processo.
        try:
            with open(self.output_file, 'w', encoding='utf-8-sig', newline='') as f_out:
                for root, dirs, files in os.walk(PROCESSED_DIR):
                    for file in files:
                        if not self._is_valid_file(file): continue
                        if file.endswith('.zip'): continue

                        filepath = os.path.join(root, file)
                        trimestre, ano = self._extract_date_info(filepath)
                        
                        try:
                            encoding = self._detect_encoding(filepath)
                            sep = self._identify_separator(filepath, encoding)
                            
                            chunks = pd.read_csv(
                                filepath, sep=sep, encoding=encoding, 
                                chunksize=CHUNK_SIZE, dtype=str, on_bad_lines='skip'
                            )

                            for chunk in chunks:
                                chunk.rename(columns=COLUMN_MAPPING, inplace=True)
                                if "Conta" not in chunk.columns: continue
                                chunk["Conta"] = chunk["Conta"].astype(str).str.strip()
                                
                                mask = chunk["Conta"].str.startswith(tuple(ACCOUNT_PREFIX_FILTER))
                                chunk = chunk[mask]
                                chunk = chunk[chunk["Conta"].str.len() == 9]

                                if chunk.empty or "Valor Despesas" not in chunk.columns: continue


                                if "Ano" not in chunk.columns and ano: chunk["Ano"] = ano
                                if "Trimestre" not in chunk.columns and trimestre: chunk["Trimestre"] = trimestre
                                
                                for col in FINAL_COLUMNS:
                                    if col not in chunk.columns: chunk[col] = ""

                                df_final = chunk[FINAL_COLUMNS].copy()

                                df_final["Valor Despesas"] = (
                                    df_final["Valor Despesas"]
                                    .astype(str).str.strip()
                                    .str.replace('.', '', regex=False)
                                    .str.replace(',', '.', regex=False)
                                )
                                df_final["Valor Despesas"] = pd.to_numeric(df_final["Valor Despesas"], errors='coerce')
                                df_final = df_final[(df_final["Valor Despesas"].notnull()) & (df_final["Valor Despesas"] != 0)]
                                
                                if "RegistroANS" in df_final.columns:
                                    df_final["RegistroANS"] = df_final["RegistroANS"].astype(str).str.replace(r'\.0$', '', regex=True)

                                if df_final.empty: continue

                                # Escreve no handle aberto
                                df_final.to_csv(
                                    f_out, header=not header_written, 
                                    index=False, sep=';', 
                                    quoting=csv.QUOTE_NONNUMERIC
                                )
                                header_written = True
                            
                            files_processed += 1
                            if files_processed % 10 == 0:
                                self.logger.info(f"   ... processados: {files_processed}")

                        except Exception as e:
                            self.logger.error(f"Erro no arquivo {file}: {e}")
        except Exception as e:
            self.logger.critical(f"Erro fatal na consolidação: {e}")
            raise

        self.logger.info(f"Consolidação Finalizada! {files_processed} arquivos processados.")
        
        # Compacta o arquivo resultante
        self.logger.info("Iniciando compactação do arquivo consolidado...")
        zip_name = os.path.basename(self.output_file).replace('.csv', '.zip')
        dest_zip = os.path.join(PROCESSED_DIR, zip_name)
        FileCompressor.compress(self.output_file, dest_zip)