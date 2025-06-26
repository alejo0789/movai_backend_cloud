# app/crud/crud_empresa.py
from typing import Optional, List
import uuid # Necesario para los UUIDs

from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import Empresa # Importa el modelo Empresa

class CRUDEmpresa(CRUDBase[Empresa]):
    """
    Clase CRUD específica para el modelo Empresa.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    como la búsqueda por NIT.
    """
    def get_by_nit(self, db: Session, nit: str) -> Optional[Empresa]:
        """
        Obtiene una empresa por su número de NIT.
        """
        return db.query(self.model).filter(self.model.nit == nit).first()

# Instancia de la clase CRUD para Empresas.
# Esta instancia será usada por los servicios y endpoints para interactuar con la tabla Empresas.
empresa_crud = CRUDEmpresa(Empresa)