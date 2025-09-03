# app/api/v1/endpoints/jetson_nanos.py
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import uuid
from datetime import datetime

# Import database session and services
from app.config.database import db 
from app.services.jetson_telemetry_service import jetson_telemetry_service
# CORRECTED IMPORTS: Importing the instance of CRUDJetsonNano
from app.crud.crud_jetson_nano import jetson_nano_crud 
# Importing create_or_update_jetson_nano from jetson_nano_service as it exists there
from app.services.jetson_nano_service import create_or_update_jetson_nano 

from app.models_db.cloud_database_models import JetsonNano, JetsonTelemetry

# Setup logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Create a Flask Blueprint for Jetson Nano endpoints
jetson_nanos_bp = Blueprint('jetson_nanos_bp', __name__)

@jetson_nanos_bp.route('/telemetry', methods=['POST'])
def receive_jetson_telemetry():
    """
    Endpoint to receive telemetry data from a Jetson Nano device.
    Expects a JSON payload with telemetry metrics.
    """
    try:
        telemetry_data = request.get_json()
        if not telemetry_data:
            logger.warning("Telemetry data received was empty or not JSON.")
            return jsonify({"message": "Invalid JSON data provided"}), 400

        # Process the telemetry data using the service layer
        processed_telemetry = jetson_telemetry_service.process_telemetry_data(db.session, telemetry_data)

        if processed_telemetry:
            return jsonify({
                "message": "Telemetry data received and processed successfully",
                "telemetry_id": str(processed_telemetry.id),
                "hardware_id": processed_telemetry.id_hardware_jetson
            }), 201
        else:
            logger.error(f"Failed to process telemetry data for {telemetry_data.get('id_hardware_jetson')}")
            return jsonify({"message": "Failed to process telemetry data"}), 500
    except Exception as e:
        logger.exception("Error receiving or processing Jetson telemetry data.")
        db.session.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
    
@jetson_nanos_bp.route('/', methods=['GET'])
def get_all_jetson_nanos_route():
    """
    Endpoint to retrieve all registered Jetson Nano devices with bus information.
    Query parameters: skip (int), limit (int).
    """
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)

        # Get all Jetson Nanos with pagination
        jetsons = jetson_nano_crud.get_multi(db.session, skip=skip, limit=limit)
        
        if jetsons:
            formatted_jetsons = []
            for jetson in jetsons:
                # Get bus information if assigned
                bus_info = None
                if jetson.id_bus and jetson.bus:
                    bus_info = {
                        "placa": jetson.bus.placa,
                        "numero_interno": jetson.bus.numero_interno,
                        "marca": jetson.bus.marca,
                        "modelo": jetson.bus.modelo,
                        "estado_operativo": jetson.bus.estado_operativo
                    }

                # Determine connection status based on last connection
                estado_conexion = "Desconectado"
                if jetson.activo:
                    if jetson.ultima_conexion_cloud_at:
                        # Check if last connection was within 10 minutes
                        time_diff = datetime.utcnow() - jetson.ultima_conexion_cloud_at
                        print(datetime.utcnow())
                        print(jetson.ultima_conexion_cloud_at)
                        print(time_diff)
                        if time_diff.total_seconds() <= 600:  # 10 minutes
                            estado_conexion = "Conectado"
                        else:
                            estado_conexion = "Desconectado"
                    else:
                        estado_conexion = "Desconectado"
                else:
                    estado_conexion = "Mantenimiento"

                formatted_jetson = {
                    "id": str(jetson.id),
                    "id_hardware_jetson": jetson.id_hardware_jetson,
                    "id_bus": str(jetson.id_bus) if jetson.id_bus else None,
                    "version_firmware": jetson.version_firmware,
                    "estado_salud": jetson.estado_salud,
                    "estado_conexion": estado_conexion,  # Calculated connection status
                    "ultima_actualizacion_firmware_at": jetson.ultima_actualizacion_firmware_at.isoformat() if jetson.ultima_actualizacion_firmware_at else None,
                    "ultima_conexion_cloud_at": jetson.ultima_conexion_cloud_at.isoformat() if jetson.ultima_conexion_cloud_at else None,
                    "last_telemetry_at": jetson.last_telemetry_at.isoformat() if jetson.last_telemetry_at else None,
                    "fecha_instalacion": jetson.fecha_instalacion.isoformat() if jetson.fecha_instalacion else None,
                    "activo": jetson.activo,
                    "observaciones": jetson.observaciones,
                    "last_updated_at": jetson.last_updated_at.isoformat(),
                    "bus_info": bus_info  # Include bus information directly
                }
                formatted_jetsons.append(formatted_jetson)
            
            return jsonify(formatted_jetsons), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        logger.exception("Error retrieving all Jetson Nano devices.")
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

# También actualizar el endpoint individual para mantener consistencia
@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['GET'])
def get_jetson_nano_details(id_hardware_jetson: str):
    """
    Endpoint to retrieve details of a specific Jetson Nano device by its hardware ID.
    """
    try:
        # Get Jetson with bus relationship loaded
        jetson = jetson_nano_crud.get_by_hardware_id(db.session, id_hardware_jetson)
        if jetson:
            # Get bus information if assigned
            bus_info = None
            if jetson.id_bus and jetson.bus:
                bus_info = {
                    "placa": jetson.bus.placa,
                    "numero_interno": jetson.bus.numero_interno,
                    "marca": jetson.bus.marca,
                    "modelo": jetson.bus.modelo,
                    "estado_operativo": jetson.bus.estado_operativo
                }

            # Determine connection status
            estado_conexion = "Desconectado"
            if jetson.activo:
                if jetson.ultima_conexion_cloud_at:
                    time_diff = datetime.utcnow() - jetson.ultima_conexion_cloud_at
                    if time_diff.total_seconds() <= 600:  # 10 minutes
                        estado_conexion = "Conectado"
                    else:
                        estado_conexion = "Desconectado"
                else:
                    estado_conexion = "Desconectado"
            else:
                estado_conexion = "Mantenimiento"

            return jsonify({
                "id": str(jetson.id),
                "id_hardware_jetson": jetson.id_hardware_jetson,
                "id_bus": str(jetson.id_bus) if jetson.id_bus else None,
                "version_firmware": jetson.version_firmware,
                "estado_salud": jetson.estado_salud,
                "estado_conexion": estado_conexion,
                "ultima_actualizacion_firmware_at": jetson.ultima_actualizacion_firmware_at.isoformat() if jetson.ultima_actualizacion_firmware_at else None,
                "ultima_conexion_cloud_at": jetson.ultima_conexion_cloud_at.isoformat() if jetson.ultima_conexion_cloud_at else None,
                "last_telemetry_at": jetson.last_telemetry_at.isoformat() if jetson.last_telemetry_at else None,
                "fecha_instalacion": jetson.fecha_instalacion.isoformat() if jetson.fecha_instalacion else None,
                "activo": jetson.activo,
                "observaciones": jetson.observaciones,
                "last_updated_at": jetson.last_updated_at.isoformat(),
                "bus_info": bus_info
            }), 200
        else:
            return jsonify({"message": "Jetson Nano not found"}), 404
    except Exception as e:
        logger.exception(f"Error retrieving Jetson Nano details for hardware ID: {id_hardware_jetson}")
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
                

@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['PUT'])
def update_jetson_nano_details(id_hardware_jetson: str):
    """
    Endpoint to update details of an existing Jetson Nano device.
    """
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({"message": "Invalid JSON data provided"}), 400

        # Fetch the existing JetsonNano object
        jetson = jetson_nano_crud.get_by_hardware_id(db.session, id_hardware_jetson)
        if not jetson:
            return jsonify({"message": "Jetson Nano not found"}), 404

        # CORRECTED: Using update method of the jetson_nano_crud instance
        # Assuming update_data is a dictionary that can be directly passed to obj_in
        updated_jetson = jetson_nano_crud.update(db.session, db_obj=jetson, obj_in=update_data) 

        if updated_jetson:
            return jsonify({
                "message": "Jetson Nano updated successfully",
                "jetson_id": str(updated_jetson.id),
                "id_hardware_jetson": updated_jetson.id_hardware_jetson
            }), 200
        else:
            return jsonify({"message": "Jetson Nano not found or update failed"}), 404
    except Exception as e:
        logger.exception(f"Error updating Jetson Nano details for hardware ID: {id_hardware_jetson}")
        db.session.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['DELETE'])
def delete_jetson_nano_route(id_hardware_jetson: str):
    """
    Endpoint to delete a Jetson Nano device.
    """
    try:
        # Fetch the existing JetsonNano object by hardware ID to get its primary ID
        jetson_to_delete = jetson_nano_crud.get_by_hardware_id(db.session, id_hardware_jetson)
        if not jetson_to_delete:
            return jsonify({"message": "Jetson Nano not found"}), 404

        # CORRECTED: Using remove method of the jetson_nano_crud instance with the primary ID
        deleted_jetson = jetson_nano_crud.remove(db.session, id=jetson_to_delete.id)
        
        if deleted_jetson: # remove method typically returns the removed object or None
            return jsonify({"message": "Jetson Nano deleted successfully"}), 204 # 204 No Content
        else:
            return jsonify({"message": "Jetson Nano not found or deletion failed"}), 404
    except Exception as e:
        logger.exception(f"Error deleting Jetson Nano device for hardware ID: {id_hardware_jetson}")
        db.session.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@jetson_nanos_bp.route('/<string:id_hardware_jetson>/telemetry/recent', methods=['GET'])
def get_recent_jetson_telemetry(id_hardware_jetson: str):
    """
    Endpoint to retrieve the most recent telemetry record for a specific Jetson Nano.
    """
    try:
        recent_telemetry = jetson_telemetry_service.get_recent_telemetry(db.session, id_hardware_jetson)
        if recent_telemetry:
            return jsonify({
                "id": str(recent_telemetry.id),
                "id_hardware_jetson": recent_telemetry.id_hardware_jetson,
                "timestamp_telemetry": recent_telemetry.timestamp_telemetry.isoformat(),
                "ram_usage_gb": float(recent_telemetry.ram_usage_gb) if recent_telemetry.ram_usage_gb else None,
                "cpu_usage_percent": float(recent_telemetry.cpu_usage_percent) if recent_telemetry.cpu_usage_percent else None,
                "disk_usage_gb": float(recent_telemetry.disk_usage_gb) if recent_telemetry.disk_usage_gb else None,
                "disk_usage_percent": float(recent_telemetry.disk_usage_percent) if recent_telemetry.disk_usage_percent else None,
                "temperatura_celsius": float(recent_telemetry.temperatura_celsius) if recent_telemetry.temperatura_celsius else None,
                "created_at": recent_telemetry.created_at.isoformat()
            }), 200
        else:
            return jsonify({"message": "No recent telemetry found for this Jetson Nano"}), 404
    except Exception as e:
        logger.exception(f"Error retrieving recent telemetry for Jetson hardware ID: {id_hardware_jetson}")
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@jetson_nanos_bp.route('/<string:id_hardware_jetson>/telemetry/history', methods=['GET'])
def get_jetson_telemetry_history(id_hardware_jetson: str):
    """
    Endpoint to retrieve historical telemetry records for a specific Jetson Nano with pagination.
    Query parameters: skip (int), limit (int).
    """
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)

        telemetry_history = jetson_telemetry_service.get_telemetry_history(db.session, id_hardware_jetson, skip=skip, limit=limit)

        if telemetry_history:
            formatted_history = []
            for record in telemetry_history:
                formatted_history.append({
                    "id": str(record.id),
                    "id_hardware_jetson": record.id_hardware_jetson,
                    "timestamp_telemetry": record.timestamp_telemetry.isoformat(),
                    "ram_usage_gb": float(record.ram_usage_gb) if record.ram_usage_gb else None,
                    "cpu_usage_percent": float(record.cpu_usage_percent) if record.cpu_usage_percent else None,
                    "disk_usage_gb": float(record.disk_usage_gb) if record.disk_usage_gb else None,
                    "disk_usage_percent": float(record.disk_usage_percent) if record.disk_usage_percent else None,
                    "temperatura_celsius": float(record.temperatura_celsius) if record.temperatura_celsius else None,
                    "created_at": record.created_at.isoformat()
                })
            return jsonify(formatted_history), 200
        else:
            return jsonify([]), 200 # Return empty list if no history found
    except Exception as e:
        logger.exception(f"Error retrieving telemetry history for Jetson hardware ID: {id_hardware_jetson}")
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
@jetson_nanos_bp.route('/<string:id_hardware_jetson>/heartbeat', methods=['POST'])


def jetson_heartbeat(id_hardware_jetson: str):
    """
    Endpoint para que las Jetson Nanos envíen un "latido" indicando que están activas.
    Actualiza ultima_conexion_cloud_at sin necesidad de enviar telemetría completa.
    """
    try:
        # Find the Jetson device
        jetson = jetson_nano_crud.get_by_hardware_id(db.session, id_hardware_jetson)
        if not jetson:
            return jsonify({"message": "Jetson Nano not found"}), 404

        # Update last connection time
        jetson.ultima_conexion_cloud_at = datetime.utcnow()
        
        # Optionally update health status if provided
        request_data = request.get_json()
        if request_data and 'estado_salud' in request_data:
            jetson.estado_salud = request_data['estado_salud']
        
        db.session.add(jetson)
        db.session.commit()
        db.session.refresh(jetson)

        logger.info(f"Heartbeat received from Jetson {id_hardware_jetson}")
        
        return jsonify({
            "message": "Heartbeat received successfully",
            "ultima_conexion_cloud_at": jetson.ultima_conexion_cloud_at.isoformat(),
            "estado_conexion": determine_connection_status(jetson)
        }), 200
        
    except Exception as e:
        logger.exception(f"Error processing heartbeat for Jetson hardware ID: {id_hardware_jetson}")
        db.session.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

def determine_connection_status(jetson: JetsonNano) -> str:
    """
    Determina el estado de conexión basado en los datos del Jetson
    
    Args:
        jetson (JetsonNano): Objeto JetsonNano de la base de datos
    
    Returns:
        str: Estado de conexión ('Conectado', 'Desconectado', 'Mantenimiento')
    """
    if not jetson.activo:
        return "Mantenimiento"
    
    if jetson.ultima_conexion_cloud_at:
        # Check if last connection was within 10 minutes
        time_diff = datetime.utcnow() - jetson.ultima_conexion_cloud_at
        if time_diff.total_seconds() <= 600:  # 10 minutes = 600 seconds
            return "Conectado"
        else:
            return "Desconectado"
    else:
        return "Desconectado"
