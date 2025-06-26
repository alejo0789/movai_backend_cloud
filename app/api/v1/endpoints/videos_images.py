# app/api/v1/endpoints/training_data.py
from flask import Blueprint, request, jsonify, send_file
from typing import Optional, List, Dict, Any
import uuid
import logging
from datetime import datetime

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para el registro de videos
from app.services.video_register_service import video_register_service # <<<<<<< IMPORTADO EL SERVICIO RENOMBRADO
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import VideoEntrenamiento, ImagenEntrenamiento

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Datos de Entrenamiento
training_data_bp = Blueprint('training_data_api', __name__)

@training_data_bp.route('/videos', methods=['POST'])
def upload_training_video():
    """
    Endpoint API para subir un video de entrenamiento para un conductor.
    El video será procesado para extraer frames y características faciales.
    Requiere: Formulario multipart/form-data con 'conductor_id' y 'video_file'.
    """
    logger.info("Solicitud recibida para subir video de entrenamiento.")
    
    conductor_id_str = request.form.get('conductor_id')
    if not conductor_id_str:
        logger.warning("Campo 'conductor_id' faltante en la solicitud de subida de video.")
        return jsonify({"message": "El 'conductor_id' es requerido."}), 400
    
    try:
        conductor_id = uuid.UUID(conductor_id_str)
    except ValueError:
        logger.warning(f"ID de conductor '{conductor_id_str}' no es un UUID válido.")
        return jsonify({"message": "El 'conductor_id' proporcionado no es un UUID válido."}), 400

    if 'video_file' not in request.files:
        logger.warning("No se encontró el archivo de video en la solicitud.")
        return jsonify({"message": "Se requiere un archivo de video ('video_file')."}), 400

    video_file = request.files['video_file']
    if video_file.filename == '':
        logger.warning("Nombre de archivo de video vacío.")
        return jsonify({"message": "Nombre de archivo de video vacío."}), 400

    db_session = db.session
    try:
        # Pasa los datos binarios del archivo al servicio
        # El servicio obtendrá la cédula del conductor para la ruta de almacenamiento
        new_video = video_register_service.upload_and_process_training_video(
            db_session, 
            conductor_id, 
            video_file.read() # Leer el contenido binario del archivo
        )

        if new_video:
            response_data = {
                "id": str(new_video.id),
                "id_conductor": str(new_video.id_conductor),
                "url_video_original": new_video.url_video_original,
                "estado_procesamiento": new_video.estado_procesamiento,
                "uploaded_at": new_video.uploaded_at.isoformat()
            }
            logger.info(f"Video de entrenamiento para conductor {conductor_id} subido y procesado exitosamente.")
            return jsonify(response_data), 201 # 201 Created
        else:
            return jsonify({"message": "Fallo al procesar el video de entrenamiento. Verifique ID de conductor o archivo."}), 400
    except Exception as e:
        logger.exception(f"Error subiendo y procesando video de entrenamiento para {conductor_id_str}: {e}")
        return jsonify({"message": "Error interno del servidor al procesar el video."}), 500


@training_data_bp.route('/videos/<uuid:conductor_id>', methods=['GET'])
def get_training_videos_by_conductor(conductor_id: uuid.UUID):
    """
    Endpoint API para obtener todos los videos de entrenamiento de un conductor.
    """
    logger.info(f"Solicitud recibida para videos de entrenamiento del conductor ID: {conductor_id}")
    db_session = db.session
    try:
        videos = video_register_service.get_videos_by_conductor(db_session, conductor_id)
        
        response_data = []
        for video in videos:
            response_data.append({
                "id": str(video.id),
                "id_conductor": str(video.id_conductor),
                "url_video_original": video.url_video_original,
                "fecha_captura": video.fecha_captura.isoformat() if video.fecha_captura else None,
                "duracion_segundos": float(video.duracion_segundos) if video.duracion_segundos is not None else None,
                "estado_procesamiento": video.estado_procesamiento,
                "uploaded_at": video.uploaded_at.isoformat()
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error obteniendo videos de entrenamiento para {conductor_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener los videos."}), 500


@training_data_bp.route('/images/<uuid:video_id>', methods=['GET'])
def get_training_images_by_video(video_id: uuid.UUID):
    """
    Endpoint API para obtener todas las imágenes (frames) de entrenamiento de un video específico.
    """
    logger.info(f"Solicitud recibida para imágenes de entrenamiento del video ID: {video_id}")
    db_session = db.session
    try:
        images = video_register_service.get_images_by_video_id(db_session, video_id)
        
        response_data = []
        for image in images:
            response_data.append({
                "id": str(image.id),
                "id_video_entrenamiento": str(image.id_video_entrenamiento),
                "url_imagen": image.url_imagen,
                "timestamp_en_video_seg": float(image.timestamp_en_video_seg) if image.timestamp_en_video_seg is not None else None,
                "es_principal": image.es_principal,
                "bounding_box_json": image.bounding_box_json,
                "caracteristicas_faciales_embedding": image.caracteristicas_faciales_embedding
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error obteniendo imágenes de entrenamiento para video {video_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener las imágenes."}), 500