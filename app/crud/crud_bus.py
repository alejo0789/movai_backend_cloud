# app/crud/crud_bus.py
from typing import Optional, List
import uuid 

from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import Bus # Importa el modelo Bus

class CRUDBus(CRUDBase[Bus]):
    """
    Clase CRUD específica para el modelo Bus.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    como la búsqueda por placa.
    """
    def get_by_placa(self, db: Session, placa: str) -> Optional[Bus]:
        """
        Obtiene un bus por su número de placa.
        """
        return db.query(self.model).filter(self.model.placa == placa).first()

    def get_buses_by_empresa(self, db: Session, empresa_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Bus]:
        """
        Obtiene una lista de buses asociados a una empresa específica.
        """
        return db.query(self.model).filter(self.model.id_empresa == empresa_id).offset(skip).limit(limit).all()

# Instancia de la clase CRUD para Buses.
# Esta instancia será usada por los servicios y endpoints para interactuar con la tabla Buses.
bus_crud = CRUDBus(Bus)