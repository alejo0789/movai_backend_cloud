# app/api/v1/endpoints/eventos.py
from flask import Blueprint, request, jsonify
from typing import Optional, List, Dict, Any
import uuid
import logging
from datetime import datetime

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para el procesamiento de Eventos
from app.services.event_processing_service import event_processing_service
# Importamos la instancia del CRUD de Eventos <<<<<<<<<<<<<<<< AÑADIDO ESTO
from app.crud.crud_evento import evento_crud 
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import Evento 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Eventos
eventos_bp = Blueprint('eventos_api', __name__)

@eventos_bp.route('/', methods=['POST'])
def receive_events_batch():
    """
    Endpoint API para recibir un lote de eventos de monitoreo desde la Jetson Nano.
    Este es el punto de entrada principal para los datos de IA.
    Requiere: Cuerpo JSON con una lista de diccionarios bajo la clave 'events'.
    """
    logger.info("Solicitud recibida para procesar un lote de eventos.")
    request_data = request.get_json()

    if not request_data or 'events' not in request_data or not isinstance(request_data['events'], list):
        logger.warning("Cuerpo JSON inválido. Se espera una lista de eventos bajo la clave 'events'.")
        return jsonify({"message": "Formato de datos inválido. Se espera {'events': [...]}"}), 400
    
    events_data: List[Dict[str, Any]] = request_data['events']
    
    if not events_data:
        logger.info("Lote de eventos vacío recibido. No hay nada que procesar.")
        return jsonify({"message": "Lote de eventos vacío. Nada que procesar."}), 200

    try:
        # Pasa la sesión gestionada por Flask-SQLAlchemy al servicio para procesar el lote
        processed_events = event_processing_service.process_events_batch(db.session, events_data)

        logger.info(f"Lote de {len(events_data)} eventos procesado exitosamente. Guardados: {len(processed_events)}")
        return jsonify({
            "message": f"Lote de {len(events_data)} eventos procesado exitosamente.",
            "processed_count": len(processed_events)
        }), 200
    except Exception as e:
        logger.exception(f"Error procesando el lote de eventos: {e}")
        return jsonify({"message": "Error interno del servidor al procesar el lote de eventos."}), 500

@eventos_bp.route('/', methods=['GET'])
def get_all_events():
    """
    Endpoint API para obtener una lista de todos los eventos con paginación y filtrado.
    Query parameters: skip (int, default 0), limit (int, default 100),
                      conductor_id (UUID str), bus_id (UUID str), session_id (UUID str).
                      También se pueden añadir filtros por tipo_evento, subtipo_evento, etc.
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    conductor_id_str = request.args.get('conductor_id')
    bus_id_str = request.args.get('bus_id')
    session_id_str = request.args.get('session_id')

    conductor_id: Optional[uuid.UUID] = None
    bus_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None # Este es el id_sesion_conduccion_jetson

    if conductor_id_str:
        try: conductor_id = uuid.UUID(conductor_id_str)
        except ValueError: return jsonify({"message": "El 'conductor_id' proporcionado no es un UUID válido."}), 400
    if bus_id_str:
        try: bus_id = uuid.UUID(bus_id_str)
        except ValueError: return jsonify({"message": "El 'bus_id' proporcionado no es un UUID válido."}), 400
    if session_id_str:
        try: session_id = uuid.UUID(session_id_str)
        except ValueError: return jsonify({"message": "El 'session_id' proporcionado no es un UUID válido."}), 400

    logger.info(f"Solicitud recibida para eventos (skip={skip}, limit={limit}, cond_id={conductor_id}, bus_id={bus_id}, sess_id={session_id}).")
    
    try:
        # Lógica de filtrado basada en los parámetros
        if conductor_id:
            eventos = evento_crud.get_events_by_conductor(db.session, conductor_id, skip=skip, limit=limit)
        elif bus_id:
            eventos = evento_crud.get_events_by_bus(db.session, bus_id, skip=skip, limit=limit)
        elif session_id:
            eventos = evento_crud.get_events_by_session(db.session, session_id, skip=skip, limit=limit)
        else: # Si no hay filtros específicos, obtener todos
            eventos = evento_crud.get_multi(db.session, skip=skip, limit=limit)
        
        response_data = []
        for evento in eventos:
            response_data.append({
                "id": str(evento.id),
                "id_bus": str(evento.id_bus),
                "id_conductor": str(evento.id_conductor) if evento.id_conductor else None,
                "id_sesion_conduccion": str(evento.id_sesion_conduccion) if evento.id_sesion_conduccion else None,
                "timestamp_evento": evento.timestamp_evento.isoformat(),
                "tipo_evento": evento.tipo_evento,
                "subtipo_evento": evento.subtipo_evento,
                "duracion_segundos": float(evento.duracion_segundos) if evento.duracion_segundos is not None else None,
                "severidad": evento.severidad,
                "confidence_score_ia": float(evento.confidence_score_ia) if evento.confidence_score_ia is not None else None,
                "alerta_disparada": evento.alerta_disparada,
                "ubicacion_gps_evento": evento.ubicacion_gps_evento,
                "snapshot_url": evento.snapshot_url, # URL a la evidencia
                "video_clip_url": evento.video_clip_url, # URL a la evidencia
                "metadatos_ia_json": evento.metadatos_ia_json,
                "sent_to_cloud_at": evento.sent_to_cloud_at.isoformat() if evento.sent_to_cloud_at else None,
                "processed_in_cloud_at": evento.processed_in_cloud_at.isoformat()
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener eventos: {e}")
        return jsonify({"message": "Error interno del servidor al obtener eventos."}), 500

# Endpoint para obtener los eventos más recientes (para dashboard, etc.)
@eventos_bp.route('/recent', methods=['GET'])
def get_recent_events():
    """
    Endpoint API para obtener los eventos más recientes.
    Query parameter: limit (int, default 50).
    """
    limit = request.args.get('limit', 50, type=int)
    logger.info(f"Solicitud recibida para los {limit} eventos más recientes.")
    try:
        eventos = evento_crud.get_recent_events(db.session, limit=limit)
        response_data = []
        for evento in eventos:
            response_data.append({
                "id": str(evento.id),
                "id_bus": str(evento.id_bus),
                "id_conductor": str(evento.id_conductor) if evento.id_conductor else None,
                "timestamp_evento": evento.timestamp_evento.isoformat(),
                "tipo_evento": evento.tipo_evento,
                "subtipo_evento": evento.subtipo_evento,
                "severidad": evento.severidad,
                "alerta_disparada": evento.alerta_disparada,
                "snapshot_url": evento.snapshot_url,
                "video_clip_url": evento.video_clip_url
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener eventos recientes: {e}")
        return jsonify({"message": "Error interno del servidor al obtener eventos recientes."}), 500