# config/settings.py
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- Obtener el directorio raíz del proyecto ---
# Asume que config/settings.py está en {PROJECT_ROOT}/config/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

class AppSettings:
    """
    Clase para manejar la configuración de la aplicación.
    Las variables se cargan desde el archivo .env o variables de entorno del sistema.
    """
    # Configuración de la base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/defaultdb")
    
    # Configuración para archivos subidos y URLs (NUEVO)
    STORAGE_PATH: str = os.path.join(PROJECT_ROOT, "uploads") # Directorio local para guardar archivos
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:5000") # URL base de tu API, necesaria para generar URLs de archivos

    # Ejemplo de otras configuraciones que podrías tener (claves JWT, modos de depuración, etc.)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_key_default") 
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Instancia de la configuración para ser usada en toda la aplicación
settings = AppSettings()