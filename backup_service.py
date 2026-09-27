import os
import zipfile
import datetime
import requests
import tempfile
import logging

logger = logging.getLogger(__name__)

def generate_backup_zip():
    """Comprime el directorio data/ en un archivo .zip y lo devuelve."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"El directorio {data_dir} no existe.")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.gettempdir()
    zip_filename = f"data_backup_{timestamp}.zip"
    zip_filepath = os.path.join(temp_dir, zip_filename)
    
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.db-journal') or file == '.DS_Store':
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=data_dir)
                zipf.write(file_path, arcname)
                
    return zip_filepath

def send_backup_to_telegram(zip_filepath: str = None):
    """Genera (o toma) un backup y lo envía a Telegram."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    
    if not token or not chat_id:
        logger.error("No se configuró TELEGRAM_TOKEN o TELEGRAM_ADMIN_CHAT_ID para el backup.")
        return
        
    cleanup_needed = False
    if not zip_filepath:
        try:
            zip_filepath = generate_backup_zip()
            cleanup_needed = True
        except Exception as e:
            logger.error(f"Error generando backup para Telegram: {e}")
            return
            
    try:
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        with open(zip_filepath, 'rb') as f:
            response = requests.post(
                url, 
                data={"chat_id": chat_id, "caption": "📦 Backup Automático de Disgraf Hub"}, 
                files={"document": f},
                timeout=60
            )
        response.raise_for_status()
        logger.info("Backup enviado exitosamente a Telegram.")
    except Exception as e:
        logger.error(f"Error enviando backup a Telegram: {e}")
    finally:
        if cleanup_needed and os.path.exists(zip_filepath):
            try:
                os.remove(zip_filepath)
            except Exception as e:
                logger.error(f"No se pudo eliminar el archivo temporal de backup: {e}")

