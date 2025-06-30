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
        Guarda el registro de telemetría y actualiza la marca de tiempo last_telemetry_at
        en la entrada del dispositivo JetsonNano correspondiente.

        Args:
            db (Session): La sesión de la base de datos.
            telemetry_data (Dict[str, Any]): Diccionario con los datos de telemetría.
                                              Esperado: id_hardware_jetson (str),
                                                        timestamp_telemetry (str ISO o datetime),
                                                        ram_usage_gb, cpu_usage_percent, disk_usage_gb,
                                                        disk_usage_percent, temperatura_celsius.

        Returns:
            Optional[JetsonTelemetry]: El objeto JetsonTelemetry creado, o None si la validación falla.
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

        try:
            # Create the new telemetry record
            new_telemetry_record = jetson_telemetry_crud.create(db, telemetry_data)

            # Update the last_telemetry_at in the JetsonNano device
            jetson_device = jetson_nano_crud.get_by_hardware_id(db, id_hardware_jetson)
            if jetson_device:
                jetson_device.last_telemetry_at = new_telemetry_record.timestamp_telemetry # Use the timestamp from the telemetry data
                db.add(jetson_device)
                db.commit() # Commit changes to JetsonNano
                db.refresh(jetson_device)
                logger.info(f"Updated last_telemetry_at for JetsonNano '{id_hardware_jetson}'.")
            else:
                logger.warning(f"JetsonNano device with hardware ID '{id_hardware_jetson}' not found. Cannot update last_telemetry_at.")

            # Commit changes for the new_telemetry_record (if not already committed by create)
            db.commit() 
            db.refresh(new_telemetry_record) # Refresh to get any DB-generated defaults/updates

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
        logger.info(f"Fetching recent telemetry for Jetson hardware ID: {id_hardware_jetson}")
        telemetry = jetson_telemetry_crud.get_recent_telemetry_for_jetson(db, id_hardware_jetson)
        if not telemetry:
            logger.warning(f"No recent telemetry found for Jetson hardware ID '{id_hardware_jetson}'.")
        return telemetry

    def get_telemetry_history(self, db: Session, id_hardware_jetson: str, skip: int = 0, limit: int = 100) -> List[JetsonTelemetry]:
        """
        Recupera un historial de registros de telemetría para un Jetson Nano específico con paginación.
        """
        logger.info(f"Fetching telemetry history for Jetson hardware ID: {id_hardware_jetson} (skip={skip}, limit={limit})")
        telemetry_history = jetson_telemetry_crud.get_telemetry_by_hardware_id(db, id_hardware_jetson, skip=skip, limit=limit)
        return telemetry_history


# Create an instance of JetsonTelemetryService
jetson_telemetry_service = JetsonTelemetryService()