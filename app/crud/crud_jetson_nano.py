# app/crud/crud_jetson_nano.py
from typing import Optional, List
import uuid

from sqlalchemy.orm import Session

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import JetsonNano # Import the JetsonNano model

class CRUDJetsonNano(CRUDBase[JetsonNano]):
    """
    CRUD class specific for the JetsonNano model.
    Inherits basic functionality from CRUDBase and adds specific methods.
    """
    def get_by_hardware_id(self, db: Session, id_hardware_jetson: str) -> Optional[JetsonNano]:
        """
        Obtiene un dispositivo Jetson Nano por su ID de hardware.
        """
        return db.query(self.model).filter(self.model.id_hardware_jetson == id_hardware_jetson).first()

    def get_jetsons_by_bus(self, db: Session, bus_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[JetsonNano]:
        """
        Obtiene una lista de dispositivos Jetson Nano asociados a un bus específico.
        """
        return db.query(self.model).filter(self.model.id_bus == bus_id).offset(skip).limit(limit).all()

# Instance of the CRUD class for JetsonNano.
jetson_nano_crud = CRUDJetsonNano(JetsonNano)
