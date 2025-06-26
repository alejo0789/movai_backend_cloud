# app/crud/crud_alerta.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc, or_ # Para ordenar y condiciones OR

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import Alerta # Importa el modelo Alerta

class CRUDAlerta(CRUDBase[Alerta]):
    """
    Clase CRUD específica para el modelo Alerta.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    para la gestión de alertas.
    """
    def get_active_alerts(self, db: Session, skip: int = 0, limit: int = 100) -> List[Alerta]:
        """
        Obtiene las alertas que están actualmente activas (estado_alerta = 'Activa').
        """
        return db.query(self.model).filter(
            self.model.estado_alerta == 'Activa'
        ).order_by(desc(self.model.timestamp_alerta)).offset(skip).limit(limit).all()

    def get_alerts_by_bus(self, db: Session, bus_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Alerta]:
        """
        Obtiene las alertas de un bus específico.
        """
        return db.query(self.model).filter(self.model.id_bus == bus_id).order_by(desc(self.model.timestamp_alerta)).offset(skip).limit(limit).all()

    def get_alerts_by_conductor(self, db: Session, conductor_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Alerta]:
        """
        Obtiene las alertas de un conductor específico.
        """
        return db.query(self.model).filter(self.model.id_conductor == conductor_id).order_by(desc(self.model.timestamp_alerta)).offset(skip).limit(limit).all()

    def get_alerts_by_session(self, db: Session, sesion_id_jetson: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Alerta]:
        """
        Obtiene las alertas para una sesión de conducción específica (usando id_sesion_conduccion_jetson).
        """
        return db.query(self.model).filter(self.model.id_sesion_conduccion == sesion_id_jetson).order_by(desc(self.model.timestamp_alerta)).offset(skip).limit(limit).all()

    def get_alerts_by_type_and_status(self, db: Session, tipo_alerta: Optional[str] = None, estado_alerta: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Alerta]:
        """
        Obtiene alertas filtradas por tipo y/o estado.
        """
        query = db.query(self.model)
        if tipo_alerta:
            query = query.filter(self.model.tipo_alerta == tipo_alerta)
        if estado_alerta:
            query = query.filter(self.model.estado_alerta == estado_alerta)
        return query.order_by(desc(self.model.timestamp_alerta)).offset(skip).limit(limit).all()

# Instancia de la clase CRUD para Alertas.
# Esta instancia será usada por los servicios y endpoints para interactuar con la tabla Alertas.
alerta_crud = CRUDAlerta(Alerta)