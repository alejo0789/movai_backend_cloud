# app/crud/crud_sesion_conduccion.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import SesionConduccion # Importa el modelo SesionConduccion

class CRUDSesionConduccion(CRUDBase[SesionConduccion]):
    """
    Clase CRUD específica para el modelo SesionConduccion.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos
    para la gestión de sesiones de conducción reales.
    """
    def get_by_jetson_session_id(self, db: Session, jetson_session_id: uuid.UUID) -> Optional[SesionConduccion]:
        """
        Obtiene una sesión de conducción por su ID global generado en la Jetson Nano.
        """
        return db.query(self.model).filter(self.model.id_sesion_conduccion_jetson == jetson_session_id).first()

    def get_active_session_for_bus(self, db: Session, bus_id: uuid.UUID) -> Optional[SesionConduccion]:
        """
        Obtiene la sesión de conducción activa actualmente para un bus específico.
        Se considera activa si fecha_fin_real es NULL y estado_sesion es 'Activa'.
        """
        return db.query(self.model).filter(
            self.model.id_bus == bus_id,
            self.model.estado_sesion == 'Activa',
            self.model.fecha_fin_real.is_(None)
        ).first()

    def get_sessions_by_conductor(self, db: Session, conductor_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[SesionConduccion]:
        """
        Obtiene las sesiones de conducción de un conductor específico, con paginación.
        """
        return db.query(self.model).filter(self.model.id_conductor == conductor_id).offset(skip).limit(limit).all()

    def get_sessions_by_bus(self, db: Session, bus_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[SesionConduccion]:
        """
        Obtiene las sesiones de conducción de un bus específico, con paginación.
        """
        return db.query(self.model).filter(self.model.id_bus == bus_id).offset(skip).limit(limit).all()

    # Podemos extender el create_or_update de CRUDBase si es necesario,
    # pero para las sesiones, cada evento de inicio/fin podría ser un PUT/POST al mismo endpoint.
    # El id_sesion_conduccion_jetson será el campo único para el upsert.

# Instancia de la clase CRUD para SesionesConduccion.
sesion_conduccion_crud = CRUDSesionConduccion(SesionConduccion)