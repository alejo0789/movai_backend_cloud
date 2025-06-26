# app/core/security.py
from passlib.context import CryptContext
import logging

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Configura el contexto de hashing de contraseñas.
# Especificamos 'bcrypt' como el esquema de hashing.
# 'deprecated="auto"' significa que bcrypt generará hashes de contraseñas con un algoritmo
# seguro por defecto y advertirá si se usa un algoritmo obsoleto.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hashea una contraseña utilizando el algoritmo bcrypt.
    
    Args:
        password (str): La contraseña en texto plano.
        
    Returns:
        str: La contraseña hasheada.
    """
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug("Contraseña hasheada con éxito.")
        return hashed_password
    except Exception as e:
        logger.error(f"Error al hashear la contraseña: {e}", exc_info=True)
        raise # Relanzar la excepción para que el servicio la maneje

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica una contraseña en texto plano contra una contraseña hasheada.
    
    Args:
        plain_password (str): La contraseña proporcionada por el usuario (en texto plano).
        hashed_password (str): La contraseña hasheada almacenada en la base de datos.
        
    Returns:
        bool: True si las contraseñas coinciden, False en caso contrario.
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        if is_valid:
            logger.debug("Verificación de contraseña exitosa.")
        else:
            logger.warning("Verificación de contraseña fallida: credenciales no válidas.")
        return is_valid
    except Exception as e:
        logger.error(f"Error al verificar la contraseña: {e}", exc_info=True)
        return False # Fallar de forma segura si hay un error en la verificación

# Ejemplo de uso (solo para pruebas, esto no se ejecutará en la app principal)
if __name__ == '__main__':
    print("--- Probando app/core/security.py ---")
    
    test_password = "MySecurePassword123!"
    
    # Hashear la contraseña
    hashed = hash_password(test_password)
    print(f"\nContraseña original: {test_password}")
    print(f"Contraseña hasheada: {hashed}")
    
    # Verificar la contraseña correcta
    is_correct = verify_password(test_password, hashed)
    print(f"Verificación (correcta): {is_correct}") # Debería ser True
    
    # Verificar una contraseña incorrecta
    is_incorrect = verify_password("WrongPassword!", hashed)
    print(f"Verificación (incorrecta): {is_incorrect}") # Debería ser False
    
    # Verificar con un hash mal formado (ej. TypeError si el hash no es str)
    is_error = verify_password(test_password, "bad_hash")
    print(f"Verificación (hash inválido): {is_error}") # Debería ser False o manejar la excepción
    
    print("--- Prueba de seguridad finalizada ---")