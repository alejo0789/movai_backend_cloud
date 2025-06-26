# app/services/user_service.py
import logging
from typing import Optional, Dict, Any, List
import uuid 

from sqlalchemy.orm import Session 

# Importar las operaciones CRUD específicas
from app.crud.crud_user import user_crud
from app.crud.crud_empresa import empresa_crud 
# Importar el módulo de seguridad para hashing de contraseñas
from app.core.security import hash_password, verify_password 
# Importar los modelos para tipado
from app.models_db.cloud_database_models import Usuario, Empresa 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class UserService:
    """
    Capa de servicio para gestionar la lógica de negocio relacionada con los Usuarios.
    Interactúa con la capa CRUD para realizar operaciones de base de datos.
    Maneja el hashing de contraseñas.
    """

    def create_new_user(self, db: Session, user_data: Dict[str, Any]) -> Optional[Usuario]:
        """
        Registra un nuevo usuario en el sistema.
        Realiza validaciones de negocio como verificar la unicidad del username/email,
        la existencia de la empresa asociada y hashea la contraseña.

        Args:
            db (Session): La sesión de la base de datos.
            user_data (Dict[str, Any]): Diccionario que contiene los datos del usuario (ej. username, email, password).

        Returns:
            Optional[Usuario]: El objeto Usuario recién creado, o None si la validación falla.
        """
        logger.info(f"Intentando crear nuevo usuario: {user_data.get('username')}")

        # Validar unicidad de username
        existing_user_by_username: Optional[Usuario] = user_crud.get_by_username(db, user_data.get('username'))
        if existing_user_by_username:
            logger.warning(f"Fallo al crear usuario: El username '{user_data.get('username')}' ya existe.")
            return None
        
        # Validar unicidad de email (si se proporciona)
        if user_data.get('email'):
            existing_user_by_email: Optional[Usuario] = user_crud.get_by_email(db, user_data.get('email'))
            if existing_user_by_email:
                logger.warning(f"Fallo al crear usuario: El email '{user_data.get('email')}' ya existe.")
                return None

        # Validar que la empresa asociada existe (si se proporciona id_empresa)
        empresa_id = user_data.get('id_empresa')
        if empresa_id:
            if isinstance(empresa_id, str):
                try:
                    empresa_id = uuid.UUID(empresa_id)
                    user_data['id_empresa'] = empresa_id 
                except ValueError:
                    logger.warning(f"Fallo al crear usuario: id_empresa '{empresa_id}' no es un UUID válido.")
                    return None
            
            empresa_existente: Optional[Empresa] = empresa_crud.get(db, empresa_id)
            if not empresa_existente:
                logger.warning(f"Fallo al crear usuario: La empresa con ID '{empresa_id}' no existe.")
                return None
        
        # --- HASHING DE CONTRASEÑA ---
        # AQUI ES EL CAMBIO: Leer 'password' del user_data
        password = user_data.get('password') 
        if not password:
            logger.warning("Fallo al crear usuario: Contraseña es requerida.")
            return None
        
        hashed_password = hash_password(password) 
        user_data['password_hash'] = hashed_password 
        
        # Remover el campo de contraseña en texto plano para no pasarlo al modelo
        # Esto es importante porque el modelo no tiene un campo 'password', solo 'password_hash'
        if 'password' in user_data:
            del user_data['password']

        try:
            new_user = user_crud.create(db, user_data)
            logger.info(f"Usuario '{new_user.username}' (ID: {new_user.id}) registrado exitosamente.")
            return new_user
        except Exception as e:
            logger.error(f"Error creando usuario '{user_data.get('username')}': {e}", exc_info=True)
            db.rollback() 
            return None

    def get_user_details(self, db: Session, user_id: uuid.UUID) -> Optional[Usuario]:
        """
        Recupera los detalles de un usuario específico por su ID.
        """
        logger.info(f"Obteniendo detalles para el usuario ID: {user_id}")
        user = user_crud.get(db, user_id)
        if not user:
            logger.warning(f"Usuario con ID '{user_id}' no encontrado.")
        return user
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[Usuario]:
        """
        Recupera un usuario por su nombre de usuario (para autenticación).
        """
        logger.info(f"Obteniendo usuario por username: {username}")
        user = user_crud.get_by_username(db, username)
        if not user:
            logger.warning(f"Usuario con username '{username}' no encontrado.")
        return user

    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Recupera una lista de todos los usuarios con paginación.
        """
        logger.info(f"Obteniendo todos los usuarios (skip={skip}, limit={limit}).")
        return user_crud.get_multi(db, skip=skip, limit=limit)
    
    def get_users_by_empresa(self, db: Session, empresa_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Recupera una lista de usuarios asociados a una empresa específica.
        """
        logger.info(f"Obteniendo usuarios para la empresa ID: {empresa_id} (skip={skip}, limit={limit}).")
        empresa_existente = empresa_crud.get(db, empresa_id)
        if not empresa_existente:
            logger.warning(f"Empresa con ID '{empresa_id}' no encontrada. No se pueden obtener sus usuarios.")
            return []
        return user_crud.get_users_by_empresa(db, empresa_id, skip=skip, limit=limit)

    def update_user_details(self, db: Session, user_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[Usuario]:
        """
        Actualiza los detalles de un usuario existente.
        Permite actualizar rol, email, activo, etc.
        Si se proporciona 'password', lo hashea.
        """
        logger.info(f"Intentando actualizar usuario ID: {user_id}")
        user_existente: Optional[Usuario] = user_crud.get(db, user_id)
        if not user_existente:
            logger.warning(f"No se puede actualizar: Usuario con ID '{user_id}' no encontrado.")
            return None
        
        # Validar si se intenta cambiar el username
        if 'username' in updates and updates['username'] != user_existente.username:
            existing_user_by_username = user_crud.get_by_username(db, updates['username'])
            if existing_user_by_username and existing_user_by_username.id != user_id:
                logger.warning(f"Fallo al actualizar usuario: El username '{updates['username']}' ya está en uso.")
                return None
        
        # Validar si se intenta cambiar el email
        if 'email' in updates and updates['email'] != user_existente.email:
            existing_user_by_email = user_crud.get_by_email(db, updates['email'])
            if existing_user_by_email and existing_user_by_email.id != user_id:
                logger.warning(f"Fallo al actualizar usuario: El email '{updates['email']}' ya está en uso.")
                return None

        # Si se proporciona una nueva contraseña, hashearla
        if 'password' in updates and updates['password']:
            updates['password_hash'] = hash_password(updates['password']) 
            del updates['password'] 
        
        # Validar existencia de la empresa si se intenta cambiar id_empresa
        if 'id_empresa' in updates and updates['id_empresa'] is not None: 
            new_empresa_id = updates['id_empresa']
            if isinstance(new_empresa_id, str):
                try: new_empresa_id = uuid.UUID(new_empresa_id)
                except ValueError: logger.warning(f"Nuevo id_empresa '{new_empresa_id}' no es UUID válido."); return None
            
            if not empresa_crud.get(db, new_empresa_id):
                logger.warning(f"Fallo al actualizar usuario: La nueva empresa con ID '{new_empresa_id}' no existe.")
                return None
            updates['id_empresa'] = new_empresa_id 

        try:
            updated_user = user_crud.update(db, user_existente, updates)
            logger.info(f"Usuario '{user_existente.username}' (ID: {user_id}) actualizado exitosamente.")
            return updated_user
        except Exception as e:
            logger.error(f"Error actualizando usuario ID '{user_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def delete_user(self, db: Session, user_id: uuid.UUID) -> bool:
        """
        Elimina un usuario del sistema.
        Considera implicaciones como usuarios asociados a alertas gestionadas.
        """
        logger.info(f"Intentando eliminar usuario ID: {user_id}")
        user_to_delete = user_crud.get(db, user_id)
        if not user_to_delete:
            logger.warning(f"No se pudo eliminar: Usuario con ID '{user_id}' no encontrado.")
            return False
        
        try:
            deleted_user = user_crud.remove(db, user_id)
            if deleted_user:
                logger.info(f"Usuario ID '{user_id}' eliminado exitosamente.")
                return True
            else:
                return False 
        except Exception as e:
            logger.error(f"Error eliminando usuario ID '{user_id}': {e}", exc_info=True)
            db.rollback()
            return False

# Crea una instancia de UserService para ser utilizada por los endpoints API.
user_service = UserService()