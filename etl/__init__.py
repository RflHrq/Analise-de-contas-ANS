# Permite que o modulo etl seja tratado como um pacote
from .scraper import ANSScraper
from .file_handler import FileHandler
from .consolidator import DataConsolidator
from .enrichment import DataEnricher
from .aggregator import DataAggregator
from .database_loader import DatabaseLoader