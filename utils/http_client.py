import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import logging
from config import HTTP_TIMEOUT, MAX_RETRIES, BACKOFF_FACTOR, HEADERS

# Desabilita o aviso de SSL inseguro (Necessário para ANS)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HttpClient:
    """
    Cliente HTTP Wrapper resiliente com suporte a Retries automáticos e Timeout.
    Padrão Singleton implícito pelo uso de requests.Session.
    """
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # Estratégia de Retry: Tenta 3 vezes se der erro 500, 502, 503, 504
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=BACKOFF_FACTOR,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        # Monta o adaptador para http e https
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.logger = logging.getLogger("ANS_ETL.HTTP")

    def get(self, url, stream=False):
        """
        Executa uma requisição GET com tratamento de erros centralizado.
        """
        try:
            # verify=False é necessário para o governo.br
            response = self.session.get(
                url, 
                timeout=HTTP_TIMEOUT, 
                verify=False, 
                stream=stream
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro HTTP ({e.response.status_code}) ao acessar {url}")
            raise
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Erro de Conexão ao acessar {url}")
            raise
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout ({HTTP_TIMEOUT}s) excedido em {url}")
            raise
        except Exception as e:
            self.logger.error(f"Erro desconhecido em GET {url}: {e}")
            raise

    def close(self):
        self.session.close()