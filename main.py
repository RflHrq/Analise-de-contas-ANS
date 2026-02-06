from asyncio.log import logger
import sys
import logging
import time
from datetime import datetime

# Importação do módulo local (garanta que a pasta 'etl' tenha um __init__.py)
try:
    from etl.scraper import ANSScraper
    from etl.consolidator import DataConsolidator
    from etl.enrichment import DataEnricher
    from etl.aggregator import DataAggregator
    from etl.database_loader import DatabaseLoader
except ImportError as e:
    print(f"Erro Crítico: Não foi possível importar o módulo ETL. Verifique a estrutura de pastas.\nDetalhe: {e}")
    sys.exit(1)

# --- Configuração de Logging ---
def setup_logger():
    """Configura o logger para output formatado no console."""
    logger = logging.getLogger("ANS_ETL")
    logger.setLevel(logging.INFO)
    
    # Formato: [HORA] [NIVEL] Mensagem
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def main():
    """
    Função principal que orquestra todo o pipeline de ETL (Extract, Transform, Load).
    
    Fluxo de Execução:
    1. Scraping: Identifica e baixa arquivos da ANS.
    2. Consolidação: Une arquivos CSV/TXT brutos.
    3. Enriquecimento: Adiciona dados cadastrais (CADOP).
    4. Agregação: Calcula KPIs e estatísticas.
    5. Carga no Banco: Salva os dados processados no PostgreSQL e gera o arquivo consolidado final.
    """
    logger = setup_logger()
    logger.info("=== Iniciando Pipeline de Extração ANS ===")
    
    start_time = time.time()
    
    try:
        # 1. Instanciação do Scraper
        scraper = ANSScraper()
        
        # 2. Etapa de Identificação (Scraping & Regex)
        logger.info("Etapa 1: Identificando trimestres disponíveis...")
        files_to_download = scraper.get_top_quarters_files(limit=3)
        
        if not files_to_download:
            logger.warning("Nenhum arquivo encontrado ou erro de conexão com a ANS.")
            sys.exit(0) 
            
        logger.info(f"Arquivos identificados: {len(files_to_download)}")
        for f in files_to_download:
            logger.info(f"   -> Encontrado: {f['filename']} (Ref: {f['quarter']}T{f['year']})")
        
        # 3. Etapa de Download e Extração
        logger.info("-" * 40)
        logger.info("Etapa 2: Iniciando Download e Extração...")
        
        success_count = 0
        failure_count = 0
        
        for item in files_to_download:
            try:
                result = scraper.download_file(item['url'], item['filename'])
                if result:
                    logger.info(f"Sucesso: {item['filename']}")
                    success_count += 1
                else:
                    logger.error(f"Falha: {item['filename']}")
                    failure_count += 1
            except Exception as e:
                logger.error(f"Erro inesperado ao processar {item['filename']}: {str(e)}")
                failure_count += 1

        logger.info("-" * 40)
        logger.info("Etapa 3: Iniciando Consolidação e Limpeza dos Dados...")
        
        consolidator = DataConsolidator()
        consolidator.process()

        # 4. Etapa de Enriquecimento
        logger.info("-" * 40)
        logger.info("Etapa 4: Enriquecimento de Dados (Cadastral)...")
        
        enricher = DataEnricher()
        # [MODIFICAÇÃO] Processamento em memória para evitar erro de disco e lock do Windows
        # save_to_disk=False evita criar o arquivo intermediário gigante que causava OSError
        df_enriched = enricher.process(save_to_disk=False)

        if df_enriched is not None and not df_enriched.empty:
            # 5. Etapa de Agregação (Summarization)
            logger.info("-" * 40)
            logger.info("Etapa 5: Agregação de Despesas (KPIs)...")
            
            aggregator = DataAggregator()
            aggregator.process(df_input=df_enriched) # Passa o DF direto

            logger.info("-" * 40)
            logger.info("Etapa 6: Carga no Banco de Dados (SQL)...")
            
            loader = DatabaseLoader()
            loader.init_db() # Cria tabelas
            loader.process(df_input=df_enriched) # Passa o DF direto
        else:
            logger.error("Falha no Enriquecimento: DataFrame vazio ou nulo.")
            sys.exit(1)

        # 6. Resumo Final
        elapsed_time = time.time() - start_time
        logger.info("-" * 40)
        logger.info(f"Processo Finalizado em {elapsed_time:.2f} segundos.")
        logger.info(f"Estatísticas: {success_count} Sucessos | {failure_count} Falhas")
        

        # Define código de saída para CI/CD (0 = Sucesso, 1 = Falha Parcial/Total)
        if failure_count > 0:
            logger.warning("O processo terminou com erros parciais.")
            sys.exit(1)
        
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\n Operação interrompida pelo usuário (CTRL+C).")
        sys.exit(130)
        
    except Exception as e:
        logger.critical(f" Erro Fatal não tratado: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()