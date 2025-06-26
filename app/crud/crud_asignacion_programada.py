# app/crud/crud_asignacion_programada.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import AsignacionProgramada 

class CRUDAsignacionProgramada(CRUDBase[AsignacionProgramada]):
    """
    Clase CRUD específica para el modelo AsignacionProgramada.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos.
    """
    def get_multi(self, db: Session, skip: int = 0, limit: int = 100, 
                  id_bus: Optional[uuid.UUID] = None, # <<<<<<<<<<<<< NUEVO PARAMETRO
                  id_conductor: Optional[uuid.UUID] = None # <<<<<<<<<<<<< NUEVO PARAMETRO
                  ) -> List[AsignacionProgramada]:
        """
        Obtiene múltiples registros con paginación y filtrado opcional por bus o conductor.
        """
        query = db.query(self.model)
        if id_bus:
            query = query.filter(self.model.id_bus == id_bus)
        if id_conductor:
            query = query.filter(self.model.id_conductor == id_conductor)
        
        return query.offset(skip).limit(limit).all()


    def get_active_assignments_for_bus(self, db: Session, bus_id: uuid.UUID) -> List[AsignacionProgramada]:
        """
        Obtiene las asignaciones programadas activas para un bus específico.
        Una asignación se considera activa si la fecha actual está entre
        fecha_inicio_programada y fecha_fin_programada (o fecha_fin_programada es NULL).
        """
        current_time = datetime.utcnow()
        return db.query(self.model).filter(
            self.model.id_bus == bus_id,
            self.model.activo == True,
            self.model.fecha_inicio_programada <= current_time,
            or_(self.model.fecha_fin_programada >= current_time, self.model.fecha_fin_programada.is_(None))
        ).all()

    def get_active_assignments_for_conductor(self, db: Session, conductor_id: uuid.UUID) -> List[AsignacionProgramada]:
        """
        Obtiene las asignaciones programadas activas para un conductor específico.
        """
        current_time = datetime.utcnow()
        return db.query(self.model).filter(
            self.model.id_conductor == conductor_id,
            self.model.activo == True,
            self.model.fecha_inicio_programada <= current_time,
            or_(self.model.fecha_fin_programada >= current_time, self.model.fecha_fin_programada.is_(None))
        ).all()

    def get_assignments_by_bus_and_date_range(self, db: Session, bus_id: uuid.UUID, start_date: datetime, end_date: datetime) -> List[AsignacionProgramada]:
        """
        Obtiene asignaciones programadas para un bus dentro de un rango de fechas.
        """
        return db.query(self.model).filter(
            self.model.id_bus == bus_id,
            self.model.fecha_inicio_programada <= end_date,
            or_(self.model.fecha_fin_programada >= start_date, self.model.fecha_fin_programada.is_(None))
        ).all()

    def get_assignments_by_conductor_and_date_range(self, db: Session, conductor_id: uuid.UUID, start_date: datetime, end_date: datetime) -> List[AsignacionProgramada]:
        """
        Obtiene asignaciones programadas para un conductor dentro de un rango de fechas.
        """
        return db.query(self.model).filter(
            self.model.id_conductor == conductor_id,
            self.model.fecha_inicio_programada <= end_date,
            or_(self.model.fecha_fin_programada >= start_date, self.model.fecha_fin_programada.is_(None))
        ).all()


# Instancia de la clase CRUD para AsignacionesProgramadas.
asignacion_programada_crud = CRUDAsignacionProgramada(AsignacionProgramada)