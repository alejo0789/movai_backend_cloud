# app/services/video_register_service.py
import logging
import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import os 
import base64 
import cv2 
import numpy as np 

from sqlalchemy.orm import Session 

# Importar CRUDs necesarios
from app.crud.crud_video_entrenamiento import video_entrenamiento_crud
from app.crud.crud_imagen_entrenamiento import imagen_entrenamiento_crud
from app.crud.crud_conductor import conductor_crud
from app.crud.crud_empresa import empresa_crud 

# Importar modelos para tipado
from app.models_db.cloud_database_models import VideoEntrenamiento, ImagenEntrenamiento, Conductor, Empresa

# Importar las configuraciones de la aplicación (para STORAGE_PATH)
from app.config.settings import settings 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# --- Configuración de almacenamiento local ---

class TrainingDataService: # Renombrar a VideoRegisterService para consistencia
    """
    Capa de servicio para gestionar la subida, procesamiento y almacenamiento
    de videos e imágenes de entrenamiento para el reconocimiento facial.
    Ahora guarda archivos localmente en el sistema de archivos.
    """

    def __init__(self):
        os.makedirs(settings.STORAGE_PATH, exist_ok=True)
        logger.info(f"Directorio de almacenamiento local: {settings.STORAGE_PATH}")


    def upload_and_process_training_video(self, db: Session, conductor_id: uuid.UUID, video_file_data: bytes) -> Optional[VideoEntrenamiento]:
        """
        Gestiona la subida de un video de entrenamiento, simula su procesamiento
        para extraer frames y características faciales, y actualiza el conductor.
        Ahora guarda los archivos localmente.

        Args:
            db (Session): Sesión de la base de datos.
            conductor_id (uuid.UUID): ID del conductor al que pertenece este video.
            video_file_data (bytes): Contenido binario del archivo de video subido.

        Returns:
            Optional[VideoEntrenamiento]: El objeto VideoEntrenamiento creado, o None si falla.
        """
        logger.info(f"Iniciando procesamiento de video de entrenamiento para conductor ID: {conductor_id}")

        conductor_existente: Optional[Conductor] = conductor_crud.get(db, conductor_id)
        if not conductor_existente:
            logger.warning(f"Conductor con ID '{conductor_id}' no encontrado. No se puede procesar el video.")
            return None
        
        conductor_cedula = conductor_existente.cedula
        if not conductor_cedula:
            logger.error(f"Conductor {conductor_id} no tiene cédula. No se puede organizar el almacenamiento.")
            return None


        # --- 1. PREPARAR DIRECTORIOS LOCALES ---
        conductor_storage_dir = os.path.join(settings.STORAGE_PATH, conductor_cedula)
        video_dir = os.path.join(conductor_storage_dir, "video")
        frames_dir = os.path.join(conductor_storage_dir, "frames")
        
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(frames_dir, exist_ok=True)
        logger.info(f"Directorios de almacenamiento para {conductor_cedula} creados: {video_dir}, {frames_dir}")


        # --- 2. ALMACENAMIENTO DE VIDEO ORIGINAL LOCALMENTE ---
        video_uuid_name = uuid.uuid4() 
        video_filename = f"training_video_{video_uuid_name}.mp4"
        local_video_path = os.path.join(video_dir, video_filename)
        
        try:
            with open(local_video_path, 'wb') as f:
                f.write(video_file_data)
            logger.info(f"Video original almacenado localmente en: {local_video_path}")
        except Exception as e:
            logger.error(f"Fallo al guardar video original localmente: {e}", exc_info=True)
            db.rollback()
            return None

        # URL para acceder al video a través del servidor Flask (se asume /static/uploads como ruta base)
        video_url = f"{settings.BASE_URL}/static/uploads/{conductor_cedula}/video/{video_filename}"


        # --- 3. REGISTRAR VIDEO EN LA BASE DE DATOS ---
        video_data = {
            "id": uuid.uuid4(), # Nuevo UUID para el registro en la BD
            "id_conductor": conductor_id,
            "url_video_original": video_url,
            "fecha_captura": datetime.utcnow().date(), 
            "duracion_segundos": 60, 
            "estado_procesamiento": "Procesado", 
            "metadata_ia_video": {"simulacion_local": "procesado_exitosamente"},
            "uploaded_at": datetime.utcnow()
        }
        new_video_entrenamiento: Optional[VideoEntrenamiento] = video_entrenamiento_crud.create(db, video_data)
        if not new_video_entrenamiento:
            logger.error(f"Fallo al registrar VideoEntrenamiento para conductor {conductor_id}.")
            os.remove(local_video_path) 
            db.rollback()
            return None
        
        # --- 4. SIMULACIÓN DE PROCESAMIENTO DE VIDEO (EXTRACCIÓN DE FRAMES Y CARACTERÍSTICAS FACIALES) ---
        simulated_frames_count = 3
        simulated_embedding = [float(i) for i in range(128)] 

        # Simulación: Crear imágenes de frames y guardar localmente
        primary_image_url = None 
        for i in range(simulated_frames_count):
            frame_uuid_name = uuid.uuid4()
            frame_filename = f"frame_{frame_uuid_name}.png"
            local_frame_path = os.path.join(frames_dir, frame_filename)
            
            dummy_frame_content = np.zeros((100, 100, 3), dtype=np.uint8) 
            es_principal_frame = (i == 0) 
            if es_principal_frame:
                dummy_frame_content = np.full((100, 100, 3), 255, dtype=np.uint8) 

            cv2.imwrite(local_frame_path, dummy_frame_content) 
            logger.info(f"Frame simulado almacenado localmente en: {local_frame_path}")

            frame_url = f"{settings.BASE_URL}/static/uploads/{conductor_cedula}/frames/{frame_filename}"
            
            imagen_data = {
                "id": uuid.uuid4(),
                "id_video_entrenamiento": new_video_entrenamiento.id,
                "url_imagen": frame_url,
                "timestamp_en_video_seg": i * (new_video_entrenamiento.duracion_segundos / simulated_frames_count),
                "es_principal": es_principal_frame,
                "bounding_box_json": {"x": 10, "y": 20, "w": 80, "h": 80}, 
                "caracteristicas_faciales_embedding": simulated_embedding if es_principal_frame else [float(x)+0.01*i for x in simulated_embedding] 
            }
            imagen_entrenamiento_crud.create(db, imagen_data) 
            logger.info(f"Imagen de entrenamiento '{frame_filename}' registrada.")
            
            if es_principal_frame:
                primary_image_url = frame_url 

        # --- 5. ACTUALIZAR CONDUCTOR CON FOTO DE PERFIL, CARACTERÍSTICAS FACIALES Y VÍNCULO AL VIDEO PRINCIPAL ---
        updates_conductor = {
            "foto_perfil_url": primary_image_url, 
            "caracteristicas_faciales_embedding": simulated_embedding,
            "id_video_entrenamiento_principal": new_video_entrenamiento.id # <<<<<<<<<<<< ¡AÑADIDA ESTA LÍNEA!
        }
        updated_conductor = conductor_crud.update(db, conductor_existente, updates_conductor)
        
        if not updated_conductor:
            logger.error(f"Fallo al actualizar conductor {conductor_id} con foto de perfil, embedding y vínculo al video. Revirtiendo.")
            db.rollback()
            if os.path.exists(conductor_storage_dir):
                import shutil
                shutil.rmtree(conductor_storage_dir) 
            return None
        
        db.commit() 
        logger.info(f"Procesamiento de video de entrenamiento completado para conductor {conductor_id}. Conductor actualizado y archivos guardados localmente.")
        return new_video_entrenamiento

# Renombrar la instancia del servicio
video_register_service = TrainingDataService()