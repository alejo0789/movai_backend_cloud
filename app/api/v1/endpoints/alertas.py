# app/api/v1/endpoints/alertas.py
from flask import Blueprint, request, jsonify
from typing import Optional, List, Dict, Any
import uuid
import logging
from datetime import datetime

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para Notificaciones de Alertas
from app.services.alert_notification_service import alert_notification_service
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import Alerta 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Alertas
alertas_bp = Blueprint('alertas_api', __name__)

@alertas_bp.route('/', methods=['GET'])
def get_all_alerts():
    """
    Endpoint API para obtener una lista de todas las alertas con paginación y filtrado.
    Query parameters: skip (int, default 0), limit (int, default 100),
                      status (str, ej. 'Activa', 'Revisada'), type (str, ej. 'Fatiga Severa').
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    status = request.args.get('status')
    alert_type = request.args.get('type')

    logger.info(f"Solicitud recibida para alertas (skip={skip}, limit={limit}, status={status}, type={alert_type}).")
    
    try:
        alertas = alert_notification_service.get_all_alerts(db.session, skip=skip, limit=limit, 
                                                            status=status, alert_type=alert_type)
        
        response_data = []
        for alerta in alertas:
            response_data.append({
                "id": str(alerta.id),
                "id_evento": str(alerta.id_evento) if alerta.id_evento else None,
                "id_conductor": str(alerta.id_conductor) if alerta.id_conductor else None,
                "id_bus": str(alerta.id_bus) if alerta.id_bus else None,
                "timestamp_alerta": alerta.timestamp_alerta.isoformat(),
                "tipo_alerta": alerta.tipo_alerta,
                "descripcion": alerta.descripcion,
                "nivel_criticidad": alerta.nivel_criticidad,
                "estado_alerta": alerta.estado_alerta,
                "gestionada_por_id_usuario": str(alerta.gestionada_por_id_usuario) if alerta.gestionada_por_id_usuario else None,
                "fecha_gestion": alerta.fecha_gestion.isoformat() if alerta.fecha_gestion else None,
                "tipo_gestion": alerta.tipo_gestion,
                "comentarios_gestion": alerta.comentarios_gestion
                # Aquí podrías añadir el snapshot_url y video_clip_url del evento asociado
                # Si el servicio get_alert_details carga el evento asociado
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener todas las alertas: {e}")
        return jsonify({"message": "Error interno del servidor al obtener las alertas."}), 500

@alertas_bp.route('/active', methods=['GET'])
def get_active_alerts():
    """
    Endpoint API para obtener una lista de alertas actualmente activas.
    Query parameters: skip (int, default 0), limit (int, default 100).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    logger.info(f"Solicitud recibida para alertas activas (skip={skip}, limit={limit}).")
    
    try:
        alertas = alert_notification_service.get_active_alerts_api(db.session, skip=skip, limit=limit)
        
        response_data = []
        for alerta in alertas:
            response_data.append({
                "id": str(alerta.id),
                "tipo_alerta": alerta.tipo_alerta,
                "descripcion": alerta.descripcion,
                "timestamp_alerta": alerta.timestamp_alerta.isoformat(),
                "id_bus": str(alerta.id_bus) if alerta.id_bus else None,
                "id_conductor": str(alerta.id_conductor) if alerta.id_conductor else None,
                "nivel_criticidad": alerta.nivel_criticidad,
                "estado_alerta": alerta.estado_alerta
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener alertas activas: {e}")
        return jsonify({"message": "Error interno del servidor al obtener las alertas activas."}), 500

@alertas_bp.route('/<uuid:alert_id>', methods=['GET'])
def get_alert_details(alert_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de una alerta específica por su ID.
    También puede incluir detalles del evento asociado (URL de evidencia).
    """
    logger.info(f"Solicitud recibida para detalles de alerta ID: {alert_id}")
    try:
        alerta = alert_notification_service.get_alert_details(db.session, alert_id)
        if alerta:
            response_data = {
                "id": str(alerta.id),
                "id_evento": str(alerta.id_evento) if alerta.id_evento else None,
                "id_conductor": str(alerta.id_conductor) if alerta.id_conductor else None,
                "id_bus": str(alerta.id_bus) if alerta.id_bus else None,
                "id_sesion_conduccion": str(alerta.id_sesion_conduccion) if alerta.id_sesion_conduccion else None,
                "timestamp_alerta": alerta.timestamp_alerta.isoformat(),
                "tipo_alerta": alerta.tipo_alerta,
                "descripcion": alerta.descripcion,
                "nivel_criticidad": alerta.nivel_criticidad,
                "estado_alerta": alerta.estado_alerta,
                "gestionada_por_id_usuario": str(alerta.gestionada_por_id_usuario) if alerta.gestionada_por_id_usuario else None,
                "fecha_gestion": alerta.fecha_gestion.isoformat() if alerta.fecha_gestion else None,
                "tipo_gestion": alerta.tipo_gestion,
                "comentarios_gestion": alerta.comentarios_gestion,
                "last_updated_at": alerta.last_updated_at.isoformat()
            }
            # Si quieres incluir los URLs del snapshot/videoclip directamente aquí,
            # necesitas cargar la relación 'evento' en el servicio y luego acceder a ella.
            # Ejemplo (si alert_notification_service.get_alert_details carga alert.evento):
            # if alerta.evento:
            #     response_data["snapshot_url"] = alerta.evento.snapshot_url
            #     response_data["video_clip_url"] = alerta.evento.video_clip_url
            
            return jsonify(response_data), 200
        else:
            logger.warning(f"Alerta ID {alert_id} no encontrada.")
            return jsonify({"message": "Alerta no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener detalles de alerta ID {alert_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener la alerta."}), 500

@alertas_bp.route('/<uuid:alert_id>', methods=['PUT'])
def update_alert_status(alert_id: uuid.UUID):
    """
    Endpoint API para actualizar el estado y los detalles de gestión de una alerta.
    Requiere: JSON con los campos a actualizar (ej. 'estado_alerta', 'tipo_gestion', 'comentarios_gestion').
    También puede incluir 'gestionada_por_id_usuario'.
    """
    logger.info(f"Solicitud recibida para actualizar alerta ID: {alert_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No se proporcionó cuerpo JSON para actualizar alerta ID {alert_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    try:
        # Se asume que el ID de usuario que gestiona la alerta se enviará en el JSON o se obtendrá del JWT
        # Por ahora, si lo envías en el JSON, usa 'gestionada_por_id_usuario'
        gestionada_por_id_usuario = updates.pop('gestionada_por_id_usuario', None) # Sacar del dict de updates
        if gestionada_por_id_usuario and isinstance(gestionada_por_id_usuario, str):
            try: gestionada_por_id_usuario = uuid.UUID(gestionada_por_id_usuario)
            except ValueError: gestionada_por_id_usuario = None # Invalid UUID

        updated_alert = alert_notification_service.update_alert_status(db.session, alert_id, updates, gestionada_por_id_usuario)
        if updated_alert:
            response_data = {
                "id": str(updated_alert.id),
                "estado_alerta": updated_alert.estado_alerta,
                "tipo_alerta": updated_alert.tipo_alerta,
                "gestionada_por_id_usuario": str(updated_alert.gestionada_por_id_usuario) if updated_alert.gestionada_por_id_usuario else None,
                "fecha_gestion": updated_alert.fecha_gestion.isoformat() if updated_alert.fecha_gestion else None,
                "tipo_gestion": updated_alert.tipo_gestion,
                "last_updated_at": updated_alert.last_updated_at.isoformat()
            }
            logger.info(f"Alerta ID {alert_id} actualizada exitosamente.")
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Alerta no encontrada o no se pudo actualizar. Verifique los datos o ID."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar alerta ID {alert_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar la alerta."}), 500

# La eliminación de alertas (DELETE) no suele ser una operación expuesta
# directamente en una API de producción para mantener el historial.
# Si fuera necesario, se añadiría aquí.