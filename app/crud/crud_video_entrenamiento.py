# app/crud/crud_video_entrenamiento.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import VideoEntrenamiento # Importa el modelo VideoEntrenamiento

class CRUDVideoEntrenamiento(CRUDBase[VideoEntrenamiento]):
    """
    Clase CRUD específica para el modelo VideoEntrenamiento.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos.
    """
    def get_videos_by_conductor(self, db: Session, conductor_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[VideoEntrenamiento]:
        """
        Obtiene videos de entrenamiento asociados a un conductor específico.
        """
        return db.query(self.model).filter(self.model.id_conductor == conductor_id).offset(skip).limit(limit).all()

    def get_pending_processing_videos(self, db: Session, limit: int = 50) -> List[VideoEntrenamiento]:
        """
        Obtiene videos de entrenamiento que están pendientes de procesamiento.
        """
        return db.query(self.model).filter(self.model.estado_procesamiento == 'Pendiente').limit(limit).all()

# Instancia de la clase CRUD para VideoEntrenamiento.
video_entrenamiento_crud = CRUDVideoEntrenamiento(VideoEntrenamiento)