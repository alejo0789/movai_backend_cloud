# app/crud/crud_evento.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc # Para ordenar resultados

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import Evento # Importa el modelo Evento

class CRUDEvento(CRUDBase[Evento]):
    """
    Clase CRUD específica para el modelo Evento.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    para la consulta de eventos.
    """
    def get_events_by_conductor(self, db: Session, conductor_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Evento]:
        """
        Obtiene una lista de eventos para un conductor específico.
        """
        return db.query(self.model).filter(self.model.id_conductor == conductor_id).offset(skip).limit(limit).all()

    def get_events_by_bus(self, db: Session, bus_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Evento]:
        """
        Obtiene una lista de eventos para un bus específico.
        """
        return db.query(self.model).filter(self.model.id_bus == bus_id).offset(skip).limit(limit).all()

    def get_events_by_session(self, db: Session, session_id_jetson: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Evento]:
        """
        Obtiene una lista de eventos para una sesión de conducción específica (usando id_sesion_conduccion_jetson de Jetson).
        """
        # Aquí, el filtro es por id_sesion_conduccion (que es la FK a id_sesion_conduccion_jetson en SesionConduccion)
        return db.query(self.model).filter(self.model.id_sesion_conduccion == session_id_jetson).offset(skip).limit(limit).all()

    def get_recent_events(self, db: Session, limit: int = 50) -> List[Evento]:
        """
        Obtiene los eventos más recientes, ordenados por timestamp_evento.
        """
        return db.query(self.model).order_by(desc(self.model.timestamp_evento)).limit(limit).all()

# Instancia de la clase CRUD para Eventos.
evento_crud = CRUDEvento(Evento)