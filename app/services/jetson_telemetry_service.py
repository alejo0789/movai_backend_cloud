# app/services/jetson_telemetry_service.py
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from sqlalchemy.orm import Session

# Import CRUDs needed
from app.crud.crud_jetson_telemetry import jetson_telemetry_crud
from app.crud.crud_jetson_nano import jetson_nano_crud
from app.models_db.cloud_database_models import JetsonTelemetry, JetsonNano

# Setup logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class JetsonTelemetryService:
    """
    Service layer for processing and storing Jetson Nano telemetry data.
    """

    def process_telemetry_data(self, db: Session, telemetry_data: Dict[str, Any]) -> Optional[JetsonTelemetry]:
        """
        Procesa los datos de telemetría entrantes de una Jetson Nano.
        Guarda el registro de telemetría y actualiza las marcas de tiempo last_telemetry_at 
        y ultima_conexion_cloud_at en la entrada del dispositivo JetsonNano correspondiente.
        """
        logger.info(f"Processing telemetry data for Jetson hardware ID: {telemetry_data.get('id_hardware_jetson')}")

        id_hardware_jetson = telemetry_data.get('id_hardware_jetson')
        if not id_hardware_jetson:
            logger.warning("Fallo al procesar telemetría: 'id_hardware_jetson' es requerido.")
            return None

        # Ensure id_hardware_jetson is a string for FK linkage if it's stored as String
        if not isinstance(id_hardware_jetson, str):
            logger.warning(f"Fallo al procesar telemetría: id_hardware_jetson '{id_hardware_jetson}' no es un string válido.")
            return None

        # Convert timestamp_telemetry to datetime if it's a string
        if 'timestamp_telemetry' in telemetry_data and isinstance(telemetry_data['timestamp_telemetry'], str):
            try:
                telemetry_data['timestamp_telemetry'] = datetime.fromisoformat(telemetry_data['timestamp_telemetry'])
            except ValueError:
                logger.warning(f"Formato de timestamp_telemetry inválido para {id_hardware_jetson}. Usando hora actual.")
                telemetry_data['timestamp_telemetry'] = datetime.utcnow()
        elif 'timestamp_telemetry' not in telemetry_data:
            telemetry_data['timestamp_telemetry'] = datetime.utcnow()

        # Convert numeric fields
        for field in ['ram_usage_gb', 'cpu_usage_percent', 'disk_usage_gb', 'disk_usage_percent', 'temperatura_celsius']:
            if field in telemetry_data and isinstance(telemetry_data[field], str):
                try:
                    telemetry_data[field] = float(telemetry_data[field])
                except ValueError:
                    telemetry_data[field] = None # Set to None if conversion fails

        # IMPORTANTE: Filtrar solo los campos que existen en el modelo JetsonTelemetry de la nube
        cloud_telemetry_fields = {
            'id_hardware_jetson': telemetry_data.get('id_hardware_jetson'),
            'timestamp_telemetry': telemetry_data.get('timestamp_telemetry'),
            'ram_usage_gb': telemetry_data.get('ram_usage_gb'),
            'cpu_usage_percent': telemetry_data.get('cpu_usage_percent'),
            'disk_usage_gb': telemetry_data.get('disk_usage_gb'),
            'disk_usage_percent': telemetry_data.get('disk_usage_percent'),
            'temperatura_celsius': telemetry_data.get('temperatura_celsius')
        }

        # Remover cualquier campo que sea None o que no deba estar en el modelo de la nube
        cloud_telemetry_data = {k: v for k, v in cloud_telemetry_fields.items() if v is not None}

        try:
            # Create the new telemetry record usando solo los campos válidos
            new_telemetry_record = jetson_telemetry_crud.create(db, cloud_telemetry_data)

            # Update BOTH last_telemetry_at AND ultima_conexion_cloud_at in the JetsonNano device
            jetson_device = jetson_nano_crud.get_by_hardware_id(db, id_hardware_jetson)
            if jetson_device:
                current_time = datetime.utcnow()
                jetson_device.last_telemetry_at = new_telemetry_record.timestamp_telemetry
                jetson_device.ultima_conexion_cloud_at = current_time  # IMPORTANTE: Actualizar conexión
                
                db.add(jetson_device)
                db.commit()
                db.refresh(jetson_device)
                logger.info(f"Updated last_telemetry_at and ultima_conexion_cloud_at for JetsonNano '{id_hardware_jetson}'.")
            else:
                logger.warning(f"JetsonNano device with hardware ID '{id_hardware_jetson}' not found. Cannot update timestamps.")

            # Commit changes for the new_telemetry_record (if not already committed by create)
            db.commit() 
            db.refresh(new_telemetry_record)

            logger.info(f"Telemetry record (ID: {new_telemetry_record.id}) processed successfully for Jetson '{id_hardware_jetson}'.")
            return new_telemetry_record
        except Exception as e:
            logger.error(f"Error processing telemetry for Jetson '{id_hardware_jetson}': {e}", exc_info=True)
            db.rollback()
            return None

    def get_recent_telemetry(self, db: Session, id_hardware_jetson: str) -> Optional[JetsonTelemetry]:
        """
        Recupera el registro de telemetría más reciente para un Jetson Nano específico.
        """
        logger.info(f"Recuperando telemetría reciente para Jetson hardware ID: {id_hardware_jetson}.")
        try:
            # Usar el método correcto del CRUD
            return jetson_telemetry_crud.get_recent_telemetry_for_jetson(db, id_hardware_jetson)
        except Exception as e:
            logger.error(f"Error recuperando telemetría reciente para Jetson '{id_hardware_jetson}': {e}", exc_info=True)
            return None

    def get_telemetry_history(self, db: Session, id_hardware_jetson: str, skip: int = 0, limit: int = 100) -> List[JetsonTelemetry]:
        """
        Recupera el historial de telemetría para un Jetson Nano específico con paginación.
        """
        logger.info(f"Recuperando historial de telemetría para Jetson hardware ID: {id_hardware_jetson} (skip={skip}, limit={limit}).")
        try:
            # Usar el método correcto del CRUD
            return jetson_telemetry_crud.get_telemetry_by_hardware_id(db, id_hardware_jetson, skip=skip, limit=limit)
        except Exception as e:
            logger.error(f"Error recuperando historial de telemetría para Jetson '{id_hardware_jetson}': {e}", exc_info=True)
            return []


# Create an instance of JetsonTelemetryService
jetson_telemetry_service = JetsonTelemetryService()
