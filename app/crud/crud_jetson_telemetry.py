# app/crud/crud_jetson_telemetry.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import JetsonTelemetry # Importa el modelo JetsonTelemetry

class CRUDJetsonTelemetry(CRUDBase[JetsonTelemetry]):
    """
    Clase CRUD específica para el modelo JetsonTelemetry.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    para la consulta de datos de telemetría de Jetson.
    """
    def get_telemetry_by_hardware_id(self, db: Session, id_hardware_jetson: str, skip: int = 0, limit: int = 100) -> List[JetsonTelemetry]:
        """
        Obtiene una lista de registros de telemetría para un Jetson Nano específico por su ID de hardware.
        """
        return db.query(self.model).filter(self.model.id_hardware_jetson == id_hardware_jetson).order_by(desc(self.model.timestamp_telemetry)).offset(skip).limit(limit).all()

    def get_recent_telemetry_for_jetson(self, db: Session, id_hardware_jetson: str) -> Optional[JetsonTelemetry]:
        """
        Obtiene el registro de telemetría más reciente para un Jetson Nano específico.
        """
        return db.query(self.model).filter(self.model.id_hardware_jetson == id_hardware_jetson).order_by(desc(self.model.timestamp_telemetry)).first()

# Instancia de la clase CRUD para JetsonTelemetry.
jetson_telemetry_crud = CRUDJetsonTelemetry(JetsonTelemetry)
