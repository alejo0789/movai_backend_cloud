# app/crud/crud_imagen_entrenamiento.py
from typing import Optional, List
import uuid
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.crud.crud_base import CRUDBase
from app.models_db.cloud_database_models import ImagenEntrenamiento # Importa el modelo ImagenEntrenamiento

class CRUDImagenEntrenamiento(CRUDBase[ImagenEntrenamiento]):
    """
    Clase CRUD específica para el modelo ImagenEntrenamiento.
    Hereda la funcionalidad básica de CRUDBase y añade métodos específicos.
    """
    def get_images_by_video_id(self, db: Session, video_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ImagenEntrenamiento]:
        """
        Obtiene imágenes de entrenamiento asociadas a un video específico.
        """
        return db.query(self.model).filter(self.model.id_video_entrenamiento == video_id).offset(skip).limit(limit).all()

    def get_principal_image_by_conductor(self, db: Session, conductor_id: uuid.UUID) -> Optional[ImagenEntrenamiento]:
        """
        Obtiene la imagen principal de entrenamiento (para reconocimiento facial) de un conductor.
        """
        # Esto requeriría una relación o subconsulta para vincular ImagenEntrenamiento a Conductor
        # a través de VideoEntrenamiento.
        # Para simplificar por ahora, si es directo, podríamos buscarla:
        # return db.query(self.model).join(VideoEntrenamiento).filter(
        #     VideoEntrenamiento.id_conductor == conductor_id,
        #     self.model.es_principal == True
        # ).first()
        
        # Como no tenemos VideoEntrenamiento aquí, la implementación más segura es buscar por video_id
        # y luego filtrar por es_principal, o que el conductor tenga una FK directa a su imagen principal.
        
        # Por ahora, simplemente devolveremos None, o si implementamos un conductor_service.get_principal_image_id
        # este CRUD lo usaría para buscar.

        logger.warning(f"get_principal_image_by_conductor: Implementación avanzada requerida para vincular ImagenEntrenamiento a Conductor.")
        # Se asume que el conductor.foto_perfil_url apunta directamente a la imagen principal.
        # Las características faciales se guardan directamente en el conductor.
        return None 

# Instancia de la clase CRUD para ImagenEntrenamiento.
imagen_entrenamiento_crud = CRUDImagenEntrenamiento(ImagenEntrenamiento)