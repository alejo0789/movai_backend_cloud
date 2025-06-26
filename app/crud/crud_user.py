# app/crud/crud_user.py
from typing import Optional, List
import uuid

from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import Usuario # Importa el modelo Usuario

class CRUDUser(CRUDBase[Usuario]):
    """
    Clase CRUD específica para el modelo Usuario.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos.
    """
    def get_by_username(self, db: Session, username: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su nombre de usuario.
        """
        return db.query(self.model).filter(self.model.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[Usuario]:
        """
        Obtiene un usuario por su dirección de email.
        """
        return db.query(self.model).filter(self.model.email == email).first()

    def get_users_by_empresa(self, db: Session, empresa_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Usuario]:
        """
        Obtiene una lista de usuarios asociados a una empresa específica.
        """
        return db.query(self.model).filter(self.model.id_empresa == empresa_id).offset(skip).limit(limit).all()

# Instancia de la clase CRUD para Usuarios.
# Esta instancia será usada por los servicios y endpoints para interactuar con la tabla Usuarios.
user_crud = CRUDUser(Usuario)