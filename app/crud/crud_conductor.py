# app/crud/crud_conductor.py
from typing import Optional, List
import uuid 

from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import Conductor # Importa el modelo Conductor

class CRUDConductor(CRUDBase[Conductor]):
    """
    Clase CRUD específica para el modelo Conductor.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    como la búsqueda por cédula o por empresa.
    """
    def get_by_cedula(self, db: Session, cedula: str) -> Optional[Conductor]:
        """
        Obtiene un conductor por su número de cédula.
        """
        return db.query(self.model).filter(self.model.cedula == cedula).first()

    def get_conductores_by_empresa(self, db: Session, empresa_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conductor]:
        """
        Obtiene una lista de conductores asociados a una empresa específica.
        """
        return db.query(self.model).filter(self.model.id_empresa == empresa_id).offset(skip).limit(limit).all()

    # Este método podría ser útil para la Jetson, pero debería venir de AsignacionProgramada
    # para saber qué conductores ESTÁN asignados a un bus. Por ahora, aquí solo se filtran por empresa.
    # def get_conductores_by_bus_id(self, db: Session, bus_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conductor]:
    #     """
    #     Obtiene una lista de conductores que están actualmente asignados a un bus específico.
    #     Esto requeriría un JOIN con la tabla de asignaciones programadas.
    #     """
    #     # Implementación posterior, o se manejará en el servicio de AsignacionesProgramadas
    #     pass


# Instancia de la clase CRUD para Conductores.
# Esta instancia será usada por los servicios y endpoints para interactuar con la tabla Conductores.
conductor_crud = CRUDConductor(Conductor)