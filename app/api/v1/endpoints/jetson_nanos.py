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

@jetson_nanos_bp.route('/', methods=['POST'])
def register_jetson_nano():
    """
    Endpoint to register a new Jetson Nano device.
    Expects a JSON payload with Jetson Nano details.
    """
    try:
        jetson_data = request.get_json()
        if not jetson_data:
            return jsonify({"message": "Invalid JSON data provided"}), 400

        # Ensure id_bus is a valid UUID if provided
        id_bus_val = None
        if 'id_bus' in jetson_data and jetson_data['id_bus']:
            try:
                id_bus_val = uuid.UUID(jetson_data['id_bus'])
            except ValueError:
                return jsonify({"message": "Invalid UUID format for id_bus"}), 400
        
        # Ensure fecha_instalacion is a valid datetime if provided
        fecha_instalacion_val = None
        if 'fecha_instalacion' in jetson_data and jetson_data['fecha_instalacion']:
            try:
                fecha_instalacion_val = datetime.fromisoformat(jetson_data['fecha_instalacion'])
            except ValueError:
                return jsonify({"message": "Invalid datetime format for fecha_instalacion"}), 400

        new_jetson = create_or_update_jetson_nano(
            db.session, 
            id_hardware_jetson=jetson_data.get('id_hardware_jetson'),
            id_bus=id_bus_val,
            version_firmware=jetson_data.get('version_firmware'),
            estado_salud=jetson_data.get('estado_salud'),
            fecha_instalacion=fecha_instalacion_val,
            activo=jetson_data.get('activo', True),
            observaciones=jetson_data.get('observaciones')
        )

        if new_jetson:
            return jsonify({
                "message": "Jetson Nano registered successfully",
                "jetson_id": str(new_jetson.id),
                "id_hardware_jetson": new_jetson.id_hardware_jetson
            }), 201
        else:
            return jsonify({"message": "Failed to register Jetson Nano"}), 500
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Jetson Nano with this hardware ID already exists or invalid data"}), 409
    except Exception as e:
        logger.exception("Error registering Jetson Nano device.")
        db.session.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500

@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['GET'])
def get_jetson_nano_details(id_hardware_jetson: str):
    """
    Endpoint to retrieve details of a specific Jetson Nano device by its hardware ID.
    """
    try:
        # CORRECTED: Using the jetson_nano_crud instance
        jetson = jetson_nano_crud.get_by_hardware_id(db.session, id_hardware_jetson) 
        if jetson:
            return jsonify({
                "id": str(jetson.id),
                "id_hardware_jetson": jetson.id_hardware_jetson,
                "id_bus": str(jetson.id_bus) if jetson.id_bus else None,
                "version_firmware": jetson.version_firmware,
                "estado_salud": jetson.estado_salud,
                "ultima_actualizacion_firmware_at": jetson.ultima_actualizacion_firmware_at.isoformat() if jetson.ultima_actualizacion_firmware_at else None,
                "ultima_conexion_cloud_at": jetson.ultima_conexion_cloud_at.isoformat() if jetson.ultima_conexion_cloud_at else None,
                "last_telemetry_at": jetson.last_telemetry_at.isoformat() if jetson.last_telemetry_at else None,
                "fecha_instalacion": jetson.fecha_instalacion.isoformat() if jetson.fecha_instalacion else None,
                "activo": jetson.activo,
                "observaciones": jetson.observaciones,
                "last_updated_at": jetson.last_updated_at.isoformat()
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

@jetson_nanos_bp.route('/', methods=['GET'])
def get_all_jetson_nanos_route():
    """
    Endpoint to retrieve all registered Jetson Nano devices.
    """
    try:
        # CORRECTED: Using get_multi method of the jetson_nano_crud instance
        jetsons = jetson_nano_crud.get_multi(db.session) 
        if jetsons:
            formatted_jetsons = []
            for jetson in jetsons:
                formatted_jetsons.append({
                    "id": str(jetson.id),
                    "id_hardware_jetson": jetson.id_hardware_jetson,
                    "id_bus": str(jetson.id_bus) if jetson.id_bus else None,
                    "version_firmware": jetson.version_firmware,
                    "estado_salud": jetson.estado_salud,
                    "ultima_actualizacion_firmware_at": jetson.ultima_actualizacion_firmware_at.isoformat() if jetson.ultima_actualizacion_firmware_at else None,
                    "ultima_conexion_cloud_at": jetson.ultima_conexion_cloud_at.isoformat() if jetson.ultima_conexion_cloud_at else None,
                    "last_telemetry_at": jetson.last_telemetry_at.isoformat() if jetson.last_telemetry_at else None,
                    "fecha_instalacion": jetson.fecha_instalacion.isoformat() if jetson.fecha_instalacion else None,
                    "activo": jetson.activo,
                    "observaciones": jetson.observaciones,
                    "last_updated_at": jetson.last_updated_at.isoformat()
                })
            return jsonify(formatted_jetsons), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        logger.exception("Error retrieving all Jetson Nano devices.")
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500