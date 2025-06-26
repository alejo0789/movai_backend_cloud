# app/api/v1/endpoints/asignaciones_programadas.py
from flask import Blueprint, request, jsonify
from typing import Optional, List
import uuid
import logging
from datetime import datetime

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para Asignaciones Programadas
from app.services.asignacion_programada_service import asignacion_programada_service
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import AsignacionProgramada 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Asignaciones Programadas
asignaciones_programadas_bp = Blueprint('asignaciones_programadas_api', __name__)

@asignaciones_programadas_bp.route('/', methods=['POST'])
def create_asignacion_programada():
    """
    Endpoint API para crear una nueva asignación programada.
    Requiere: JSON con 'id_conductor' (UUID str), 'id_bus' (UUID str),
              'fecha_inicio_programada' (str ISO), 'fecha_fin_programada' (str ISO, opcional),
              'tipo_programacion' (str).
    """
    logger.info("Solicitud recibida para crear una nueva asignación programada.")
    asignacion_data = request.get_json()

    if not asignacion_data:
        logger.warning("No se proporcionó cuerpo JSON para la asignación programada.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los datos de la asignación programada."}), 400
    
    required_fields = ['id_conductor', 'id_bus', 'fecha_inicio_programada', 'tipo_programacion']
    if not all(field in asignacion_data for field in required_fields):
        logger.warning(f"Faltan campos requeridos para la asignación programada: {required_fields}.")
        return jsonify({"message": f"Los campos {required_fields} son requeridos."}), 400

    try:
        new_asignacion = asignacion_programada_service.create_new_asignacion_programada(db.session, asignacion_data)

        if new_asignacion:
            response_data = {
                "id": str(new_asignacion.id),
                "id_conductor": str(new_asignacion.id_conductor),
                "id_bus": str(new_asignacion.id_bus),
                "fecha_inicio_programada": new_asignacion.fecha_inicio_programada.isoformat(),
                "fecha_fin_programada": new_asignacion.fecha_fin_programada.isoformat() if new_asignacion.fecha_fin_programada else None,
                "tipo_programacion": new_asignacion.tipo_programacion,
                "activo": new_asignacion.activo
            }
            logger.info(f"Asignación programada {new_asignacion.id} creada exitosamente.")
            return jsonify(response_data), 201 
        else:
            return jsonify({"message": "Fallo al crear la asignación programada. Verifique IDs de conductor/bus o fechas."}), 400
    except Exception as e:
        logger.exception(f"Error creando asignación programada: {e}")
        return jsonify({"message": "Error interno del servidor al crear la asignación programada."}), 500

@asignaciones_programadas_bp.route('/<uuid:asignacion_id>', methods=['GET'])
def get_asignacion_details(asignacion_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de una asignación programada específica por su ID.
    """
    logger.info(f"Solicitud recibida para detalles de asignación programada ID: {asignacion_id}")
    try:
        asignacion = asignacion_programada_service.get_asignacion_details(db.session, asignacion_id)
        if asignacion:
            response_data = {
                "id": str(asignacion.id),
                "id_conductor": str(asignacion.id_conductor),
                "id_bus": str(asignacion.id_bus),
                "fecha_inicio_programada": asignacion.fecha_inicio_programada.isoformat(),
                "fecha_fin_programada": asignacion.fecha_fin_programada.isoformat() if asignacion.fecha_fin_programada else None,
                "tipo_programacion": asignacion.tipo_programacion,
                "turno_especifico": asignacion.turno_especifico,
                "activo": asignacion.activo,
                "last_updated_at": asignacion.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Asignación programada ID {asignacion_id} no encontrada.")
            return jsonify({"message": "Asignación programada no encontrada."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener detalles de asignación programada ID {asignacion_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener la asignación programada."}), 500

@asignaciones_programadas_bp.route('/', methods=['GET'])
def get_all_asignaciones_programadas():
    """
    Endpoint API para obtener una lista de todas las asignaciones programadas con paginación.
    Query parameters: skip (int, default 0), limit (int, default 100),
                      bus_id (UUID str, opcional), conductor_id (UUID str, opcional).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    # >>>>>>>>>>>>>>> CAMBIO AQUI: bus_id_str y conductor_id_str como query parameters <<<<<<<<<<<<<<<
    bus_id_str = request.args.get('bus_id') # Usar 'bus_id' como en la petición
    conductor_id_str = request.args.get('conductor_id') # Usar 'conductor_id' como en la petición

    bus_id: Optional[uuid.UUID] = None
    conductor_id: Optional[uuid.UUID] = None

    if bus_id_str:
        try: bus_id = uuid.UUID(bus_id_str)
        except ValueError: return jsonify({"message": "El 'bus_id' proporcionado no es un UUID válido."}), 400
    if conductor_id_str:
        try: conductor_id = uuid.UUID(conductor_id_str)
        except ValueError: return jsonify({"message": "El 'conductor_id' proporcionado no es un UUID válido."}), 400

    logger.info(f"Solicitud recibida para asignaciones programadas (skip={skip}, limit={limit}, bus_id={bus_id}, conductor_id={conductor_id}).")
    
    try:
        # Pasa los filtros directamente al servicio
        asignaciones = asignacion_programada_service.get_all_asignaciones_programadas(
            db.session, 
            skip=skip, 
            limit=limit,
            id_bus=bus_id, # <<<<<<<<<<<<<<<< PASANDO EL ID DEL BUS
            id_conductor=conductor_id # <<<<<<<<<<<<<<<< PASANDO EL ID DEL CONDUCTOR
        )

        response_data = []
        for asignacion in asignaciones:
            response_data.append({
                "id": str(asignacion.id),
                "id_conductor": str(asignacion.id_conductor),
                "id_bus": str(asignacion.id_bus),
                "fecha_inicio_programada": asignacion.fecha_inicio_programada.isoformat(),
                "fecha_fin_programada": asignacion.fecha_fin_programada.isoformat() if asignacion.fecha_fin_programada else None,
                "tipo_programacion": asignacion.tipo_programacion,
                "activo": asignacion.activo
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener todas las asignaciones programadas: {e}")
        return jsonify({"message": "Error interno del servidor al obtener las asignaciones programadas."}), 500


@asignaciones_programadas_bp.route('/<uuid:asignacion_id>', methods=['PUT'])
def update_asignacion_programada_details(asignacion_id: uuid.UUID):
    """
    Endpoint API para actualizar los detalles de una asignación programada existente.
    Requiere: JSON con los campos a actualizar.
    """
    logger.info(f"Solicitud recibida para actualizar asignación programada ID: {asignacion_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No se proporcionó cuerpo JSON para actualizar asignación ID {asignacion_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    try:
        updated_asignacion = asignacion_programada_service.update_asignacion_programada_details(db.session, asignacion_id, updates)
        if updated_asignacion:
            response_data = {
                "id": str(updated_asignacion.id),
                "id_conductor": str(updated_asignacion.id_conductor),
                "id_bus": str(updated_asignacion.id_bus),
                "fecha_inicio_programada": updated_asignacion.fecha_inicio_programada.isoformat(),
                "fecha_fin_programada": updated_asignacion.fecha_fin_programada.isoformat() if updated_asignacion.fecha_fin_programada else None,
                "tipo_programacion": updated_asignacion.tipo_programacion,
                "activo": updated_asignacion.activo,
                "last_updated_at": updated_asignacion.last_updated_at.isoformat()
            }
            logger.info(f"Asignación programada ID {asignacion_id} actualizada exitosamente.")
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Asignación programada no encontrada o no se pudo actualizar. Verifique los datos o ID."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar asignación programada ID {asignacion_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar la asignación programada."}), 500

@asignaciones_programadas_bp.route('/<uuid:asignacion_id>', methods=['DELETE'])
def delete_asignacion_programada(asignacion_id: uuid.UUID):
    """
    Endpoint API para eliminar una asignación programada del sistema.
    """
    logger.info(f"Solicitud recibida para eliminar asignación programada ID: {asignacion_id}")
    try:
        deleted = asignacion_programada_service.delete_asignacion_programada(db.session, asignacion_id)
        if deleted:
            logger.info(f"Asignación programada ID {asignacion_id} eliminada exitosamente.")
            return jsonify({"message": "Asignación programada eliminada correctamente."}), 204 
        else:
            return jsonify({"message": "Asignación programada no encontrada o no se pudo eliminar."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar asignación programada ID {asignacion_id}: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar la asignación programada."}), 500