# app/api/v1/endpoints/jetson_nanos.py
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import uuid

# Import database session and services
from app.config.database import db 
from app.services.jetson_telemetry_service import jetson_telemetry_service
from app.services.jetson_nano_service import jetson_nano_service # Assuming you'll create this service soon
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
    db = next(get_db()) # Get a database session
    try:
        telemetry_data = request.get_json()
        if not telemetry_data:
            logger.warning("Telemetry data received was empty or not JSON.")
            return jsonify({"message": "Invalid JSON data provided"}), 400

        # Process the telemetry data using the service layer
        processed_telemetry = jetson_telemetry_service.process_telemetry_data(db, telemetry_data)

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
        db.rollback() # Rollback in case of an error
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close() # Close the database session

@jetson_nanos_bp.route('/', methods=['POST'])
def register_jetson_nano():
    """
    Endpoint to register a new Jetson Nano device.
    Expects a JSON payload with Jetson Nano details.
    """
    db = next(get_db())
    try:
        jetson_data = request.get_json()
        if not jetson_data:
            return jsonify({"message": "Invalid JSON data provided"}), 400

        # Use the jetson_nano_service to create the device
        new_jetson = jetson_nano_service.create_jetson_nano(db, jetson_data)

        if new_jetson:
            return jsonify({
                "message": "Jetson Nano registered successfully",
                "jetson_id": str(new_jetson.id),
                "id_hardware_jetson": new_jetson.id_hardware_jetson
            }), 201
        else:
            return jsonify({"message": "Failed to register Jetson Nano"}), 500
    except IntegrityError:
        db.rollback()
        return jsonify({"message": "Jetson Nano with this hardware ID already exists or invalid data"}), 409
    except Exception as e:
        logger.exception("Error registering Jetson Nano device.")
        db.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()

@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['GET'])
def get_jetson_nano_details(id_hardware_jetson: str):
    """
    Endpoint to retrieve details of a specific Jetson Nano device by its hardware ID.
    """
    db = next(get_db())
    try:
        jetson = jetson_nano_service.get_jetson_nano_by_hardware_id(db, id_hardware_jetson)
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
    finally:
        db.close()

@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['PUT'])
def update_jetson_nano_details(id_hardware_jetson: str):
    """
    Endpoint to update details of an existing Jetson Nano device.
    """
    db = next(get_db())
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({"message": "Invalid JSON data provided"}), 400

        updated_jetson = jetson_nano_service.update_jetson_nano(db, id_hardware_jetson, update_data)

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
        db.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()

@jetson_nanos_bp.route('/<string:id_hardware_jetson>', methods=['DELETE'])
def delete_jetson_nano(id_hardware_jetson: str):
    """
    Endpoint to delete a Jetson Nano device.
    """
    db = next(get_db())
    try:
        deleted_count = jetson_nano_service.delete_jetson_nano(db, id_hardware_jetson)
        if deleted_count > 0:
            return jsonify({"message": "Jetson Nano deleted successfully"}), 200
        else:
            return jsonify({"message": "Jetson Nano not found"}), 404
    except Exception as e:
        logger.exception(f"Error deleting Jetson Nano device for hardware ID: {id_hardware_jetson}")
        db.rollback()
        return jsonify({"message": f"Internal server error: {str(e)}"}), 500
    finally:
        db.close()

@jetson_nanos_bp.route('/<string:id_hardware_jetson>/telemetry/recent', methods=['GET'])
def get_recent_jetson_telemetry(id_hardware_jetson: str):
    """
    Endpoint to retrieve the most recent telemetry record for a specific Jetson Nano.
    """
    db = next(get_db())
    try:
        recent_telemetry = jetson_telemetry_service.get_recent_telemetry(db, id_hardware_jetson)
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
    finally:
        db.close()

@jetson_nanos_bp.route('/<string:id_hardware_jetson>/telemetry/history', methods=['GET'])
def get_jetson_telemetry_history(id_hardware_jetson: str):
    """
    Endpoint to retrieve historical telemetry records for a specific Jetson Nano with pagination.
    Query parameters: skip (int), limit (int).
    """
    db = next(get_db())
    try:
        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)

        telemetry_history = jetson_telemetry_service.get_telemetry_history(db, id_hardware_jetson, skip=skip, limit=limit)

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
    finally:
        db.close()

@jetson_nanos_bp.route('/', methods=['GET'])
def get_all_jetson_nanos():
    """
    Endpoint to retrieve all registered Jetson Nano devices.
    """
    db = next(get_db())
    try:
        jetsons = jetson_nano_service.get_all_jetson_nanos(db)
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
    finally:
        db.close()