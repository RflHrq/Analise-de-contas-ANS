import zipfile
import os
import logging

class FileCompressor:
    """
    Classe utilitária responsável por compactar arquivos.
    Centraliza a lógica de ZIP para evitar duplicação de código.
    """
    
    @staticmethod
    def compress(source_path: str, destination_path: str):
        """
        Compacta um arquivo único em formato .zip.
        
        Args:
            source_path (str): Caminho completo do arquivo original (ex: .csv).
            destination_path (str): Caminho completo onde o .zip será salvo.
        """
        logger = logging.getLogger("ANS_ETL.Compressor")
        
        if not os.path.exists(source_path):
            logger.error(f"Arquivo fonte não encontrado para compressão: {source_path}")
            return False

        # Garante que o diretório de destino exista
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        logger.info(f"Compactando: {os.path.basename(source_path)} -> {os.path.basename(destination_path)}...")
        
        try:
            with zipfile.ZipFile(destination_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # arcname=os.path.basename garante que o ZIP não guarde a estrutura de pastas completa
                zf.write(source_path, arcname=os.path.basename(source_path))
            
            logger.info("Compactação concluída com sucesso.")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao compactar arquivo: {e}")
            return False