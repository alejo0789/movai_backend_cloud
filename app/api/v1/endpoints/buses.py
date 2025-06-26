# app/api/v1/endpoints/buses.py
from flask import Blueprint, request, jsonify
from typing import Optional, List
import uuid
import logging

# Importamos la instancia de la base de datos de Flask-SQLAlchemy
from app.config.database import db 
# Importamos la capa de servicio para Buses
from app.services.bus_service import bus_service
# Importamos la capa de servicio para Conductores (AHORA SÍ ES REAL)
from app.services.conductor_service import conductor_service # <<<<<<< DESCOMENTADO Y USADO
# Importamos los modelos para poder devolver objetos tipados
from app.models_db.cloud_database_models import Bus, Conductor 

# Setup logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Creamos un Blueprint para los endpoints de Buses
buses_bp = Blueprint('buses_api', __name__)

@buses_bp.route('/', methods=['POST'])
def register_bus():
    """
    Endpoint API para registrar un nuevo bus.
    Requiere: Cuerpo JSON con 'placa' (str), 'numero_interno' (str), 'id_empresa' (UUID str).
    """
    logger.info("Solicitud recibida para registrar un nuevo bus.")
    bus_data = request.get_json()

    if not bus_data:
        logger.warning("No se proporcionó cuerpo JSON para el registro del bus.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los datos del bus."}), 400
    
    # Validación básica de campos requeridos
    if 'placa' not in bus_data or 'numero_interno' not in bus_data or 'id_empresa' not in bus_data:
        logger.warning("Faltan campos requeridos para el registro del bus.")
        return jsonify({"message": "Los campos 'placa', 'numero_interno' e 'id_empresa' son requeridos."}), 400

    try:
        # Pasa la sesión gestionada por Flask-SQLAlchemy al servicio
        new_bus = bus_service.register_new_bus(db.session, bus_data)

        if new_bus:
            response_data = {
                "id": str(new_bus.id),
                "placa": new_bus.placa,
                "numero_interno": new_bus.numero_interno,
                "id_empresa": str(new_bus.id_empresa),
                "estado_operativo": new_bus.estado_operativo
            }
            logger.info(f"Bus '{new_bus.placa}' registrado exitosamente.")
            return jsonify(response_data), 201 # 201 Created
        else:
            return jsonify({"message": "Fallo al registrar el bus. Verifique los datos o la empresa asociada."}), 400
    except Exception as e:
        logger.exception(f"Error registrando bus: {e}")
        return jsonify({"message": "Error interno del servidor al registrar el bus."}), 500

@buses_bp.route('/<uuid:bus_id>', methods=['GET'])
def get_bus_details(bus_id: uuid.UUID):
    """
    Endpoint API para obtener los detalles de un bus específico por su ID.
    """
    logger.info(f"Solicitud recibida para detalles del bus ID: {bus_id}")
    try:
        bus = bus_service.get_bus_details(db.session, bus_id)
        if bus:
            response_data = {
                "id": str(bus.id),
                "id_empresa": str(bus.id_empresa),
                "placa": bus.placa,
                "numero_interno": bus.numero_interno,
                "marca": bus.marca,
                "modelo": bus.modelo,
                "anio_fabricacion": bus.anio_fabricacion,
                "capacidad_pasajeros": bus.capacidad_pasajeros,
                "estado_operativo": bus.estado_operativo,
                "ultima_conexion_at": bus.ultima_conexion_at.isoformat() if bus.ultima_conexion_at else None,
                "ubicacion_actual_gps": bus.ubicacion_actual_gps,
                "last_updated_at": bus.last_updated_at.isoformat()
            }
            return jsonify(response_data), 200
        else:
            logger.warning(f"Bus ID {bus_id} no encontrado.")
            return jsonify({"message": "Bus no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener detalles del bus ID {bus_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener el bus."}), 500

@buses_bp.route('/by_placa', methods=['GET'])
def get_bus_by_placa():
    """
    Endpoint API para que la Jetson Nano obtenga la información de un bus por su placa.
    Query parameter: placa (str).
    """
    placa = request.args.get('placa')
    if not placa:
        logger.warning("No se proporcionó la placa para buscar el bus.")
        return jsonify({"message": "El parámetro 'placa' es requerido."}), 400
    
    logger.info(f"Solicitud recibida para el bus con placa: {placa}")
    try:
        bus = bus_service.get_bus_by_placa_logic(db.session, placa)
        if bus:
            response_data = {
                "id": str(bus.id),
                "id_empresa": str(bus.id_empresa),
                "placa": bus.placa,
                "numero_interno": bus.numero_interno,
                "marca": bus.marca,
                "modelo": bus.modelo,
                "anio_fabricacion": bus.anio_fabricacion,
                "capacidad_pasajeros": bus.capacidad_pasajeros,
                "estado_operativo": bus.estado_operativo,
                "ultima_conexion_at": bus.ultima_conexion_at.isoformat() if bus.ultima_conexion_at else None,
                "ubicacion_actual_gps": bus.ubicacion_actual_gps,
                "last_updated_at": bus.last_updated_at.isoformat()
            }
            logger.info(f"Bus '{placa}' encontrado y detalles enviados.")
            return jsonify(response_data), 200
        else:
            logger.warning(f"Bus con placa '{placa}' no encontrado.")
            return jsonify({"message": "Bus no encontrado."}), 404
    except Exception as e:
        logger.exception(f"Error al obtener bus por placa {placa}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener el bus por placa."}), 500

@buses_bp.route('/<uuid:bus_id>/drivers', methods=['GET'])
def get_bus_drivers(bus_id: uuid.UUID):
    """
    Endpoint API para que la Jetson Nano obtenga los conductores asignados a un bus específico.
    """
    logger.info(f"Solicitud recibida para conductores asignados al bus ID: {bus_id}")
    try:
        # Verificar si el bus existe primero
        bus_existente = bus_service.get_bus_details(db.session, bus_id)
        if not bus_existente:
            logger.warning(f"Bus ID {bus_id} no encontrado para obtener sus conductores.")
            return jsonify({"message": "Bus no encontrado."}), 404

        # >>>>>>>>>>>>>>>>> REEMPLAZANDO MOCK CON LÓGICA REAL <<<<<<<<<<<<<<<<<
        # Utiliza el servicio de conductor para obtener los conductores asociados
        conductores: List[Conductor] = conductor_service.get_conductores_by_bus(db.session, bus_id)
        
        response_data = []
        for conductor in conductores:
            response_data.append({
                "id": str(conductor.id),
                "id_empresa": str(conductor.id_empresa),
                "cedula": conductor.cedula,
                "nombre_completo": conductor.nombre_completo,
                "codigo_qr_hash": conductor.codigo_qr_hash,
                "activo": conductor.activo,
                # NOTA: características_faciales_embedding podría ser grande o sensible.
                # Considera si realmente necesitas enviarlo a la Jetson o si basta con un hash/ID.
                # Si lo envías, asegúrate de que sea JSON serializable.
                "caracteristicas_faciales_embedding": conductor.caracteristicas_faciales_embedding 
            })
        
        logger.info(f"Devolviendo {len(conductores)} conductores para el bus {bus_id}.")
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener conductores para el bus ID {bus_id}: {e}")
        return jsonify({"message": "Error interno del servidor al obtener los conductores del bus."}), 500


@buses_bp.route('/', methods=['GET'])
def get_all_buses():
    """
    Endpoint API para obtener una lista de todos los buses con paginación.
    Query parameters: skip (int, default 0), limit (int, default 100), empresa_id (UUID str, opcional).
    """
    skip = request.args.get('skip', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    empresa_id_str = request.args.get('empresa_id')
    empresa_id: Optional[uuid.UUID] = None

    if empresa_id_str:
        try:
            empresa_id = uuid.UUID(empresa_id_str)
        except ValueError:
            return jsonify({"message": "El 'empresa_id' proporcionado no es un UUID válido."}), 400

    logger.info(f"Solicitud recibida para todos los buses (skip={skip}, limit={limit}, empresa_id={empresa_id}).")
    
    try:
        if empresa_id:
            buses = bus_service.get_buses_by_empresa(db.session, empresa_id, skip=skip, limit=limit)
        else:
            buses = bus_service.get_all_buses(db.session, skip=skip, limit=limit)
        
        response_data = []
        for bus in buses:
            response_data.append({
                "id": str(bus.id),
                "id_empresa": str(bus.id_empresa),
                "placa": bus.placa,
                "numero_interno": bus.numero_interno,
                "estado_operativo": bus.estado_operativo
            })
        return jsonify(response_data), 200
    except Exception as e:
        logger.exception(f"Error al obtener todos los buses: {e}")
        return jsonify({"message": "Error interno del servidor al obtener los buses."}), 500

@buses_bp.route('/<uuid:bus_id>', methods=['PUT'])
def update_bus_details(bus_id: uuid.UUID):
    """
    Endpoint API para actualizar los detalles de un bus existente.
    Requiere: Cuerpo JSON con los campos a actualizar.
    """
    logger.info(f"Solicitud recibida para actualizar bus ID: {bus_id}")
    updates = request.get_json()

    if not updates:
        logger.warning(f"No se proporcionó cuerpo JSON para actualizar el bus ID {bus_id}.")
        return jsonify({"message": "Se requiere un cuerpo JSON con los campos a actualizar."}), 400

    try:
        updated_bus = bus_service.update_bus_details(db.session, bus_id, updates)
        if updated_bus:
            response_data = {
                "id": str(updated_bus.id),
                "placa": updated_bus.placa,
                "numero_interno": updated_bus.numero_interno,
                "estado_operativo": updated_bus.estado_operativo,
                "last_updated_at": updated_bus.last_updated_at.isoformat()
            }
            logger.info(f"Bus ID {bus_id} actualizado exitosamente.")
            return jsonify(response_data), 200
        else:
            return jsonify({"message": "Bus no encontrado o no se pudo actualizar. Verifique los datos o ID."}), 404
    except Exception as e:
        logger.exception(f"Error al actualizar bus ID {bus_id}: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar el bus."}), 500

@buses_bp.route('/<uuid:bus_id>', methods=['DELETE'])
def delete_bus(bus_id: uuid.UUID):
    """
    Endpoint API para eliminar un bus del sistema.
    """
    logger.info(f"Solicitud recibida para eliminar bus ID: {bus_id}")
    try:
        deleted = bus_service.delete_bus(db.session, bus_id)
        if deleted:
            logger.info(f"Bus ID {bus_id} eliminado exitosamente.")
            return jsonify({"message": "Bus eliminado correctamente."}), 204 
        else:
            return jsonify({"message": "Bus no encontrado o no se pudo eliminar (puede tener registros asociados)."}), 404
    except Exception as e:
        logger.exception(f"Error al eliminar bus ID {bus_id}: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar el bus."}), 500