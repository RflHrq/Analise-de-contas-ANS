import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Imports novos
from config import ANS_BASE_URL
from utils.http_client import HttpClient
from .file_handler import FileHandler

class ANSScraper:
    """
    Responsável pela lógica de negócio da extração (Business Logic),
    delegando a infraestrutura para HttpClient e FileHandler.
    """
    
    def __init__(self):
        self.client = HttpClient() # Injeção da dependência de rede
        self.file_handler = FileHandler()
        self.base_url = ANS_BASE_URL

    def _get_soup(self, url):
        """Helper para obter o BeautifulSoup de uma URL."""
        try:
            response = self.client.get(url)
            return BeautifulSoup(response.text, 'html.parser')
        except Exception:
            return None # O log já foi feito no HttpClient

    def _detect_quarter(self, filename):
        filename = filename.lower()
        patterns = [
            r'(\d)t(\d{4})', r'(\d{4})[-_](\d)t', r'(\d{4})_(\d)_trimestre',
        ]
        for pat in patterns:
            match = re.search(pat, filename)
            if match:
                g1, g2 = match.groups()
                if len(g1) == 4: return int(g1), int(g2)
                else: return int(g2), int(g1)
        return None

    def get_top_quarters_files(self, limit=3):
        """
        Navega no site da ANS para identificar os arquivos trimestrais mais recentes.
        
        Args:
            limit (int): Número máximo de trimestres para retornar.
            
        Retorna:
            list: Lista de dicionários com metadados dos arquivos encontrados.
        """
        print(f" Mapeando estrutura do repositório: {self.base_url}")
        soup = self._get_soup(self.base_url)
        if not soup: return []

        
        links = soup.find_all('a')
        years = []
        for l in links:
            href = l.get('href')
            if href and re.match(r'^\d{4}/?$', href.strip()):
                years.append(int(href.strip('/')))
        years.sort(reverse=True)
        
        candidates = []
        for year in years[:3]:
            year_url = urljoin(self.base_url, f"{year}/")
            year_soup = self._get_soup(year_url)
            if not year_soup: continue
            
            file_links = year_soup.find_all('a')
            for f_link in file_links:
                href = f_link.get('href')
                if not href or not href.lower().endswith('.zip'): continue
                detected = self._detect_quarter(href)
                if detected and detected[0] == year:
                    candidates.append({
                        'year': detected[0], 'quarter': detected[1],
                        'url': urljoin(year_url, href), 'filename': href
                    })

        unique_quarters = sorted(list(set((c['year'], c['quarter']) for c in candidates)), reverse=True)[:limit]
        final_files = [c for c in candidates if (c['year'], c['quarter']) in unique_quarters]
        return final_files

    def download_file(self, url, filename):
        """
        Baixa um arquivo específico, com suporte a stream e barra de progresso simples.
        Descompacta automaticamente após o download.
        
        Args:
            url (str): URL de origem.
            filename (str): Nome do arquivo local.
            
        Retorna:
            str: Caminho do arquivo local baixado, ou None em caso de falha.
        """
        """Baixa usando o HttpClient com stream."""
        local_path = os.path.join(self.file_handler.download_dir, filename)
        
        if os.path.exists(local_path):
            print(f"   Arquivo já existe: {filename}")
            self.file_handler.extract_zip(local_path)
            return local_path

        print(f" Baixando {filename}...", end='', flush=True)
        try:
            # Aqui usamos o get com stream=True do nosso wrapper
            with self.client.get(url, stream=True) as r:
                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
            print(" Concluído.")
            
            self.file_handler.extract_zip(local_path)
            return local_path
        except Exception as e:
            print(f" Falha (ver log).")
            if os.path.exists(local_path): os.remove(local_path)
            return None