# app/api/v1/endpoints/conductores.py
from flask import Blueprint, request, jsonify, send_file # <<<<<<< send_file importado
from typing import Optional, List
import uuid
import logging
from datetime import datetime

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para Conductores
from app.services.conductor_service import conductor_service
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import Conductor 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Conductores
conductores_bp = Blueprint('conductores_api', __name__)

@conductores_bp.route('/', methods=['POST'])
def register_conductor():
    """
    Endpoint API para registrar un nuevo conductor.
    Requiere: Cuerpo JSON con 'cedula' (str), 'nombre_completo' (str), 'id_empresa' (UUID str).
    """
    logger.info("Solicitud recibida para registrar un nuevo conductor.")
    conductor_data = request.get_json()

    if not conductor_data:
        logger.warning("No se proporcionó cuerpo JSON para el registro del conductor.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los datos del conductor."}), 400
    
    required_fields = ['cedula', 'nombre_completo', 'id_empresa']
    if not all(field in conductor_data for field in required_fields):
        logger.warning(f"Faltan campos requeridos para el registro del conductor: {required_fields}.")
        return jsonify({"message": f"Los campos {required_fields} son requeridos."}), 400

    try:
        new_conductor = conductor_service.register_new_conductor(db.session, conductor_data)

        if new_conductor:
            response_data = {
                "id": str(new_conductor.id),
                "cedula": new_conductor.cedula,
                "nombre_completo": new_conductor.nombre_completo,
                "id_empresa": str(new_conductor.id_empresa),
                "activo": new_conductor.activo
            }
            logger.info(f"Conductor '{new_conductor.nombre_completo}' registrado exitosamente.")
            return jsonify(response_data), 201 
        else:
            return jsonify({"message": "Fallo al registrar el conductor. Verifique los datos o la empresa asociada."}), 400
    except Exception as e:
        logger.exception(f"Error registrando conductor: {e}")
        return jsonify({"message": "Error interno del servidor al registrar el conductor."}), 500

@conductores_bp.route('/<uuid:conductor_id>', methods=['GET'])
def get_conductor_details(conductor_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de un conductor específico por su ID.
    """
    logger.info(f"Solicitud recibida para detalles del conductor ID: {conductor_id}")
    try:
        conductor = conductor_service.get_conductor_details(db.session, conductor_id)
        if conductor:
            response_data = {
                "id": str(conductor.id),
                "id_empresa": str(conductor.id_empresa),
                "cedula": conductor.cedula,
                "nombre_completo": conductor.nombre_completo,
                "fecha_nacimiento": conductor.fecha_nacimiento.isoformat() if conductor.fecha_nacimiento else None,
                "telefono_contacto": conductor.telefono_contacto,
                "email": conductor.email,
                "licencia_conduccion": conductor.licencia_conduccion,
                "tipo_licencia": conductor.tipo_licencia,
                "fecha_expiracion_licencia": conductor.fecha_expiracion_licencia.isoformat() if conductor.fecha_expiracion_licencia else None,
                "activo": conductor.activo,
                "codigo_qr_hash": conductor.codigo_qr_hash,
                "foto_perfil_url": conductor.foto_perfil_url,
                "last_updated_at": conductor.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Conductor ID {conductor_id} no encontrado.")
            return jsonify({"message": "Conductor no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener detalles del conductor ID {conductor_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener el conductor."}), 500

@conductores_bp.route('/by_cedula', methods=['GET'])
def get_conductor_by_cedula():
    """
    Endpoint API para obtener los detalles de un conductor por su cédula.
    Query parameter: cedula (str).
    """
    cedula = request.args.get('cedula')
    if not cedula:
        logger.warning("No se proporcionó la cédula para buscar el conductor.")
        return jsonify({"message": "El parámetro 'cedula' es requerido."}), 400
    
    logger.info(f"Solicitud recibida para el conductor con cédula: {cedula}")
    try:
        conductor = conductor_service.get_conductor_by_cedula_logic(db.session, cedula)
        if conductor:
            response_data = {
                "id": str(conductor.id),
                "id_empresa": str(conductor.id_empresa),
                "cedula": conductor.cedula,
                "nombre_completo": conductor.nombre_completo,
                "activo": conductor.activo,
                "codigo_qr_hash": conductor.codigo_qr_hash
            }
            logger.info(f"Conductor con cédula '{cedula}' encontrado y detalles enviados.")
            return jsonify(response_data), 200
        else:
            logger.warning(f"Conductor con cédula '{cedula}' no encontrado.")
            return jsonify({"message": "Conductor no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener conductor por cédula {cedula}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener el conductor por cédula."}), 500


@conductores_bp.route('/', methods=['GET'])
def get_all_conductores():
    """
    Endpoint API para obtener una lista de todos los conductores con paginación.
    Query parameters: skip (int, default 0), limit (int, default 100), id_empresa (UUID str, opcional).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    empresa_id_str = request.args.get('id_empresa')
    empresa_id: Optional[uuid.UUID] = None

    if empresa_id_str:
        try:
            empresa_id = uuid.UUID(empresa_id_str)
        except ValueError:
            return jsonify({"message": "El 'id_empresa' proporcionado no es un UUID válido."}), 400

    logger.info(f"Solicitud recibida para todos los conductores (skip={skip}, limit={limit}, id_empresa={empresa_id}).")
    
    try:
        if empresa_id:
            conductores = conductor_service.get_conductores_by_empresa(db.session, empresa_id, skip=skip, limit=limit)
        else:
            conductores = conductor_service.get_all_conductores(db.session, skip=skip, limit=limit)
        
        response_data = []
        for conductor in conductores:
            response_data.append({
                "id": str(conductor.id),
                "id_empresa": str(conductor.id_empresa),
                "cedula": conductor.cedula,
                "nombre_completo": conductor.nombre_completo,
                "activo": conductor.activo
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener todos los conductores: {e}")
        return jsonify({"message": "Error interno del servidor al obtener los conductores."}), 500

@conductores_bp.route('/<uuid:conductor_id>', methods=['PUT'])
def update_conductor_details(conductor_id: uuid.UUID):
    """
    Endpoint API para actualizar los detalles de un conductor existente.
    Requiere: Cuerpo JSON con los campos a actualizar.
    """
    logger.info(f"Solicitud recibida para actualizar conductor ID: {conductor_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No se proporcionó cuerpo JSON para actualizar el conductor ID {conductor_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    try:
        updated_conductor = conductor_service.update_conductor_details(db.session, conductor_id, updates)
        if updated_conductor:
            response_data = {
                "id": str(updated_conductor.id),
                "cedula": updated_conductor.cedula,
                "nombre_completo": updated_conductor.nombre_completo,
                "activo": updated_conductor.activo,
                "last_updated_at": updated_conductor.last_updated_at.isoformat()
            }
            logger.info(f"Conductor ID {conductor_id} actualizado exitosamente.")
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Conductor no encontrado o no se pudo actualizar. Verifique los datos o ID."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar conductor ID {conductor_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar el conductor."}), 500

@conductores_bp.route('/<uuid:conductor_id>', methods=['DELETE'])
def delete_conductor(conductor_id: uuid.UUID):
    """
    Endpoint API para eliminar un conductor del sistema.
    """
    logger.info(f"Solicitud recibida para eliminar conductor ID: {conductor_id}")
    try:
        deleted = conductor_service.delete_conductor(db.session, conductor_id)
        if deleted:
            logger.info(f"Conductor ID {conductor_id} eliminado exitosamente.")
            return jsonify({"message": "Conductor eliminado correctamente."}), 204 
        else:
            return jsonify({"message": "Conductor no encontrado o no se pudo eliminar (puede tener registros asociados)."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar conductor ID {conductor_id}: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar el conductor."}), 500

@conductores_bp.route('/<uuid:conductor_id>/qr', methods=['GET'])
def get_conductor_qr(conductor_id: uuid.UUID):
    """
    Endpoint API para obtener el código QR de un conductor específico.
    Devuelve la imagen del QR como un archivo PNG.
    """
    logger.info(f"Solicitud recibida para obtener QR del conductor ID: {conductor_id}")
    db_session = db.session
    try:
        qr_image_stream = conductor_service.generate_qr_code_for_conductor(db_session, conductor_id)
        if qr_image_stream:
            # send_file es una función de Flask para enviar archivos
            return send_file(qr_image_stream, mimetype='image/png', as_attachment=False, download_name=f"qr_{conductor_id}.png")
        else:
            return jsonify({"message": "No se pudo generar el QR para el conductor especificado."}), 404
    except Exception as e:
        logger.exception(f"Error generando QR para conductor {conductor_id}: {e}")
        return jsonify({"message": "Error interno del servidor al generar el QR."}), 500