import os
import zipfile
import shutil
from config import RAW_DIR, PROCESSED_DIR 


class FileHandler:
    """
    Gerencia operações de sistema de arquivos: criação de diretórios e extração de ZIPs.
    """
    def __init__(self):
        """
        Inicializa o manipulador e define os diretórios de trabalho.
        """
        self.download_dir = RAW_DIR
        self.extract_dir = PROCESSED_DIR
        self._create_dirs()

    def _create_dirs(self):
        """Cria os diretórios necessários se não existirem."""
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            os.makedirs(self.extract_dir, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Falha ao criar diretórios de trabalho: {e}")

    def extract_zip(self, zip_path):
        """
        Extrai um arquivo ZIP para o diretório de processamento.
        Retorna o caminho da pasta extraída ou None em caso de erro.
        """
        if not os.path.exists(zip_path):
            print(f"   [ERRO] Arquivo não encontrado para extração: {zip_path}")
            return None

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Cria uma pasta dedicada para o conteúdo do ZIP
                folder_name = os.path.splitext(os.path.basename(zip_path))[0]
                target_path = os.path.join(self.extract_dir, folder_name)
                
                # Limpa a pasta alvo se já existir para evitar mistura de dados antigos
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                
                os.makedirs(target_path, exist_ok=True)
                zip_ref.extractall(target_path)
                
                print(f"Extraído em: {target_path}")
                return target_path
                
        except zipfile.BadZipFile:
            print(f"Arquivo ZIP corrompido: {zip_path}")
            return None
        except Exception as e:
            print(f"Erro inesperado na extração: {e}")
            return None