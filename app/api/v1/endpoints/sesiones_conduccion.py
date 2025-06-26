# app/api/v1/endpoints/sesiones_conduccion.py
from flask import Blueprint, request, jsonify
from typing import Optional, List
import uuid
import logging
from datetime import datetime

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para Sesiones de Conducción
from app.services.sesion_conduccion_service import sesion_conduccion_service
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import SesionConduccion 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Sesiones de Conducción
sesiones_conduccion_bp = Blueprint('sesiones_conduccion_api', __name__)

@sesiones_conduccion_bp.route('/', methods=['POST'])
def receive_session_data():
    """
    Endpoint API para recibir datos de sesión de conducción (inicio o fin) desde la Jetson Nano.
    Este endpoint es crucial para la sincronización de las sesiones en tiempo real.
    Requiere: JSON con 'id_sesion_conduccion_jetson' (UUID str), 'id_conductor' (UUID str),
              'id_bus' (UUID str), 'fecha_inicio_real' (str ISO), 'estado_sesion' (str).
              'fecha_fin_real' (str ISO, opcional), 'duracion_total_seg' (num, opcional).
    """
    logger.info("Solicitud recibida para procesar datos de sesión de conducción.")
    session_data = request.get_json()

    if not session_data:
        logger.warning("No se proporcionó cuerpo JSON para los datos de sesión.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los datos de la sesión."}), 400
    
    # Validación básica de campos requeridos para la creación/actualización de sesión
    required_fields = ['id_sesion_conduccion_jetson', 'id_conductor', 'id_bus', 'fecha_inicio_real', 'estado_sesion']
    if not all(field in session_data for field in required_fields):
        logger.warning(f"Faltan campos requeridos para los datos de sesión: {required_fields}.")
        return jsonify({"message": f"Los campos {required_fields} son requeridos."}), 400

    try:
        # Pasa la sesión gestionada por Flask-SQLAlchemy al servicio
        processed_session = sesion_conduccion_service.process_incoming_session_data(db.session, session_data)

        if processed_session:
            response_data = {
                "id": str(processed_session.id), # ID de la BD central
                "id_sesion_conduccion_jetson": str(processed_session.id_sesion_conduccion_jetson), # ID original de la Jetson
                "id_conductor": str(processed_session.id_conductor),
                "id_bus": str(processed_session.id_bus),
                "fecha_inicio_real": processed_session.fecha_inicio_real.isoformat(),
                "fecha_fin_real": processed_session.fecha_fin_real.isoformat() if processed_session.fecha_fin_real else None,
                "estado_sesion": processed_session.estado_sesion
            }
            logger.info(f"Datos de sesión '{processed_session.id_sesion_conduccion_jetson}' procesados y guardados exitosamente.")
            return jsonify(response_data), 200 # 200 OK para creación o actualización
        else:
            return jsonify({"message": "Fallo al procesar los datos de la sesión de conducción. Verifique los datos o IDs."}), 400
    except Exception as e:
        logger.exception(f"Error procesando datos de sesión: {e}")
        return jsonify({"message": "Error interno del servidor al procesar la sesión de conducción."}), 500

@sesiones_conduccion_bp.route('/<uuid:sesion_id>', methods=['GET'])
def get_sesion_details(sesion_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de una sesión de conducción específica por su ID central.
    """
    logger.info(f"Solicitud recibida para detalles de sesión de conducción ID: {sesion_id}")
    try:
        sesion = sesion_conduccion_service.get_sesion_details(db.session, sesion_id)
        if sesion:
            response_data = {
                "id": str(sesion.id),
                "id_sesion_conduccion_jetson": str(sesion.id_sesion_conduccion_jetson),
                "id_conductor": str(sesion.id_conductor),
                "id_bus": str(sesion.id_bus),
                "fecha_inicio_real": sesion.fecha_inicio_real.isoformat(),
                "fecha_fin_real": sesion.fecha_fin_real.isoformat() if sesion.fecha_fin_real else None,
                "estado_sesion": sesion.estado_sesion,
                "duracion_total_seg": float(sesion.duracion_total_seg) if sesion.duracion_total_seg is not None else None,
                "last_updated_at": sesion.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Sesión de conducción ID {sesion_id} no encontrada.")
            return jsonify({"message": "Sesión de conducción no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener detalles de sesión de conducción ID {sesion_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener la sesión."}), 500

@sesiones_conduccion_bp.route('/by_jetson_id/<uuid:jetson_session_id>', methods=['GET'])
def get_sesion_by_jetson_id(jetson_session_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de una sesión de conducción
    por su ID generado en la Jetson Nano.
    """
    logger.info(f"Solicitud recibida para sesión por Jetson ID: {jetson_session_id}")
    try:
        sesion = sesion_conduccion_service.get_sesion_by_jetson_id(db.session, jetson_session_id)
        if sesion:
            response_data = {
                "id": str(sesion.id),
                "id_sesion_conduccion_jetson": str(sesion.id_sesion_conduccion_jetson),
                "id_conductor": str(sesion.id_conductor),
                "id_bus": str(sesion.id_bus),
                "fecha_inicio_real": sesion.fecha_inicio_real.isoformat(),
                "fecha_fin_real": sesion.fecha_fin_real.isoformat() if sesion.fecha_fin_real else None,
                "estado_sesion": sesion.estado_sesion,
                "duracion_total_seg": float(sesion.duracion_total_seg) if sesion.duracion_total_seg is not None else None,
                "last_updated_at": sesion.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Sesión de Jetson ID {jetson_session_id} no encontrada.")
            return jsonify({"message": "Sesión de conducción por Jetson ID no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener sesión por Jetson ID {jetson_session_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener la sesión por Jetson ID."}), 500


@sesiones_conduccion_bp.route('/active', methods=['GET'])
def get_active_sessions():
    """
    Endpoint API para obtener una lista de todas las sesiones de conducción actualmente activas.
    Query parameters: skip (int, default 0), limit (int, default 100).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    logger.info(f"Solicitud recibida para sesiones activas (skip={skip}, limit={limit}).")
    
    try:
        sesiones = sesion_conduccion_service.get_active_sessions(db.session, skip=skip, limit=limit)
        
        response_data = []
        for sesion in sesiones:
            response_data.append({
                "id": str(sesion.id),
                "id_sesion_conduccion_jetson": str(sesion.id_sesion_conduccion_jetson),
                "id_conductor": str(sesion.id_conductor),
                "id_bus": str(sesion.id_bus),
                "fecha_inicio_real": sesion.fecha_inicio_real.isoformat(),
                "estado_sesion": sesion.estado_sesion
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener sesiones activas: {e}")
        return jsonify({"message": "Error interno del servidor al obtener las sesiones activas."}), 500

@sesiones_conduccion_bp.route('/by_bus/<uuid:bus_id>', methods=['GET'])
def get_sessions_by_bus(bus_id: uuid.UUID):
    """
    Endpoint API para obtener una lista de sesiones de conducción para un bus específico.
    Query parameters: skip (int, default 0), limit (int, default 100).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    logger.info(f"Solicitud recibida para sesiones del bus ID: {bus_id} (skip={skip}, limit={limit}).")
    try:
        sesiones = sesion_conduccion_service.get_sessions_by_bus(db.session, bus_id, skip=skip, limit=limit)
        
        response_data = []
        for sesion in sesiones:
            response_data.append({
                "id": str(sesion.id),
                "id_sesion_conduccion_jetson": str(sesion.id_sesion_conduccion_jetson),
                "id_conductor": str(sesion.id_conductor),
                "id_bus": str(sesion.id_bus),
                "fecha_inicio_real": sesion.fecha_inicio_real.isoformat(),
                "fecha_fin_real": sesion.fecha_fin_real.isoformat() if sesion.fecha_fin_real else None,
                "estado_sesion": sesion.estado_sesion
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener sesiones por bus: {e}")
        return jsonify({"message": "Error interno del servidor al obtener sesiones por bus."}), 500

@sesiones_conduccion_bp.route('/by_conductor/<uuid:conductor_id>', methods=['GET'])
def get_sessions_by_conductor(conductor_id: uuid.UUID):
    """
    Endpoint API para obtener una lista de sesiones de conducción para un conductor específico.
    Query parameters: skip (int, default 0), limit (int, default 100).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    logger.info(f"Solicitud recibida para sesiones del conductor ID: {conductor_id} (skip={skip}, limit={limit}).")
    try:
        sesiones = sesion_conduccion_service.get_sessions_by_conductor(db.session, conductor_id, skip=skip, limit=limit)
        
        response_data = []
        for sesion in sesiones:
            response_data.append({
                "id": str(sesion.id),
                "id_sesion_conduccion_jetson": str(sesion.id_sesion_conduccion_jetson),
                "id_conductor": str(sesion.id_conductor),
                "id_bus": str(sesion.id_bus),
                "fecha_inicio_real": sesion.fecha_inicio_real.isoformat(),
                "fecha_fin_real": sesion.fecha_fin_real.isoformat() if sesion.fecha_fin_real else None,
                "estado_sesion": sesion.estado_sesion
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener sesiones por conductor: {e}")
        return jsonify({"message": "Error interno del servidor al obtener sesiones por conductor."}), 500

@sesiones_conduccion_bp.route('/<uuid:sesion_id>', methods=['PUT'])
def update_sesion_details(sesion_id: uuid.UUID):
    """
    Endpoint API para actualizar los detalles de una sesión de conducción existente
    por su ID primario de la nube.
    Requiere: JSON con los campos a actualizar.
    """
    logger.info(f"Solicitud recibida para actualizar sesión de conducción ID: {sesion_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No se proporcionó cuerpo JSON para actualizar sesión ID {sesion_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    try:
        updated_sesion = sesion_conduccion_service.update_sesion_details(db.session, sesion_id, updates)
        if updated_sesion:
            response_data = {
                "id": str(updated_sesion.id),
                "id_sesion_conduccion_jetson": str(updated_sesion.id_sesion_conduccion_jetson),
                "estado_sesion": updated_sesion.estado_sesion,
                "fecha_fin_real": updated_sesion.fecha_fin_real.isoformat() if updated_sesion.fecha_fin_real else None,
                "duracion_total_seg": float(updated_sesion.duracion_total_seg) if updated_sesion.duracion_total_seg is not None else None,
                "last_updated_at": updated_sesion.last_updated_at.isoformat()
            }
            logger.info(f"Sesión de conducción ID {sesion_id} actualizada exitosamente.")
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Sesión de conducción no encontrada o no se pudo actualizar. Verifique los datos o ID."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar sesión de conducción ID {sesion_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar la sesión."}), 500

@sesiones_conduccion_bp.route('/<uuid:sesion_id>', methods=['DELETE'])
def delete_sesion(sesion_id: uuid.UUID):
    """
    Endpoint API para eliminar una sesión de conducción del sistema.
    Normalmente, las sesiones no se eliminan, solo se marcan como 'Finalizada' o 'Inactiva'.
    """
    logger.info(f"Solicitud recibida para eliminar sesión de conducción ID: {sesion_id}")
    try:
        deleted = sesion_conduccion_service.delete_sesion(db.session, sesion_id)
        if deleted:
            logger.info(f"Sesión de conducción ID {sesion_id} eliminada exitosamente.")
            return jsonify({"message": "Sesión de conducción eliminada correctamente."}), 204 # 204 No Content
        else:
            return jsonify({"message": "Sesión de conducción no encontrada o no se pudo eliminar."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar sesión de conducción ID {sesion_id}: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar la sesión."}), 500