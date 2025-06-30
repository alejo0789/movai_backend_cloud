import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging

# Import the cloud database models
# Assuming your cloud database models are in a path like 'app.models_db.cloud_database_models'
from app.models_db.cloud_database_models import JetsonNano, JetsonTelemetry, Bus

# Configure logger for this service
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def create_or_update_jetson_nano(
    db: Session,
    id_hardware_jetson: str,
    id_bus: Optional[uuid.UUID] = None,
    version_firmware: Optional[str] = None,
    estado_salud: Optional[str] = None,
    fecha_instalacion: Optional[datetime] = None,
    activo: bool = True,
    observaciones: Optional[str] = None
) -> Optional[JetsonNano]:
    """
    Crea un nuevo registro de JetsonNano en la base de datos de la nube,
    o actualiza uno existente si el id_hardware_jetson ya existe.
    Esta función es idempotente.

    Args:
        db: Sesión de la base de datos.
        id_hardware_jetson: El ID único del hardware de la Jetson Nano.
        id_bus: El UUID del bus al que está asignada esta Jetson (opcional).
        version_firmware: Versión del firmware actual (opcional).
        estado_salud: Estado de salud reportado (opcional).
        fecha_instalacion: Fecha de instalación (opcional).
        activo: Si la Jetson está activa (por defecto True).
        observaciones: Cualquier observación adicional (opcional).

    Returns:
        JetsonNano: El objeto JetsonNano creado o actualizado, o None si falla.
    """
    logger.info(f"Attempting to create or update JetsonNano with hardware ID: {id_hardware_jetson}")
    try:
        jetson = db.query(JetsonNano).filter(JetsonNano.id_hardware_jetson == id_hardware_jetson).first()

        if jetson:
            # Update existing JetsonNano record
            logger.debug(f"JetsonNano with hardware ID {id_hardware_jetson} found. Updating...")
            jetson.id_bus = id_bus
            jetson.version_firmware = version_firmware if version_firmware is not None else jetson.version_firmware
            jetson.estado_salud = estado_salud if estado_salud is not None else jetson.estado_salud
            jetson.ultima_conexion_cloud_at = datetime.utcnow() # Update last connection timestamp
            jetson.activo = activo
            jetson.observaciones = observaciones if observaciones is not None else jetson.observaciones
            # last_updated_at is handled by SQLAlchemy's onupdate

            # Check if id_bus exists in the Bus table if provided
            if id_bus:
                bus_exists = db.query(Bus).filter(Bus.id == id_bus).first()
                if not bus_exists:
                    logger.warning(f"Bus with ID {id_bus} not found in cloud database for JetsonNano {id_hardware_jetson}. Setting id_bus to None.")
                    jetson.id_bus = None # Prevent foreign key error if bus doesn't exist
            
            db.commit()
            db.refresh(jetson)
            logger.info(f"JetsonNano {id_hardware_jetson} updated successfully.")
            return jetson
        else:
            # Create new JetsonNano record
            logger.debug(f"JetsonNano with hardware ID {id_hardware_jetson} not found. Creating new record.")
            
            # Check if id_bus exists in the Bus table if provided
            if id_bus:
                bus_exists = db.query(Bus).filter(Bus.id == id_bus).first()
                if not bus_exists:
                    logger.warning(f"Bus with ID {id_bus} not found in cloud database for new JetsonNano {id_hardware_jetson}. Setting id_bus to None.")
                    id_bus = None # Prevent foreign key error if bus doesn't exist

            new_jetson = JetsonNano(
                id_hardware_jetson=id_hardware_jetson,
                id_bus=id_bus,
                version_firmware=version_firmware,
                estado_salud=estado_salud,
                ultima_conexion_cloud_at=datetime.utcnow(),
                fecha_instalacion=fecha_instalacion if fecha_instalacion is not None else datetime.utcnow(),
                activo=activo,
                observaciones=observaciones
            )
            db.add(new_jetson)
            db.commit()
            db.refresh(new_jetson)
            logger.info(f"New JetsonNano {id_hardware_jetson} created successfully.")
            return new_jetson

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError when creating/updating JetsonNano {id_hardware_jetson}: {e.orig}", exc_info=True)
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError when creating/updating JetsonNano {id_hardware_jetson}: {e}", exc_info=True)
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating/updating JetsonNano {id_hardware_jetson}: {e}", exc_info=True)
        return None

def create_jetson_telemetry_record(
    db: Session,
    id_hardware_jetson: str,
    timestamp_telemetry: datetime,
    ram_usage_gb: Optional[float] = None,
    cpu_usage_percent: Optional[float] = None,
    disk_usage_gb: Optional[float] = None,
    disk_usage_percent: Optional[float] = None,
    temperatura_celsius: Optional[float] = None
) -> Optional[JetsonTelemetry]:
    """
    Crea un nuevo registro de telemetría para una Jetson Nano específica en la base de datos de la nube.

    Args:
        db: Sesión de la base de datos.
        id_hardware_jetson: El ID de hardware de la Jetson a la que pertenece esta telemetría.
        timestamp_telemetry: La marca de tiempo cuando se recopiló esta telemetría.
        ram_usage_gb: Uso de RAM en GB (opcional).
        cpu_usage_percent: Uso de CPU en porcentaje (opcional).
        disk_usage_gb: Uso de disco en GB (opcional).
        disk_usage_percent: Uso de disco en porcentaje (opcional).
        temperatura_celsius: Temperatura en grados Celsius (opcional).

    Returns:
        JetsonTelemetry: El objeto JetsonTelemetry creado, o None si falla.
    """
    logger.info(f"Attempting to create telemetry record for Jetson: {id_hardware_jetson}")
    try:
        # Ensure the JetsonNano exists before creating telemetry
        # This is a critical check to maintain foreign key integrity.
        # If the JetsonNano doesn't exist, telemetry for it cannot be saved.
        jetson_exists = db.query(JetsonNano).filter(JetsonNano.id_hardware_jetson == id_hardware_jetson).first()
        if not jetson_exists:
            logger.error(f"JetsonNano with hardware ID {id_hardware_jetson} not found. Cannot save telemetry.")
            return None

        new_telemetry = JetsonTelemetry(
            id_hardware_jetson=id_hardware_jetson,
            timestamp_telemetry=timestamp_telemetry,
            ram_usage_gb=ram_usage_gb,
            cpu_usage_percent=cpu_usage_percent,
            disk_usage_gb=disk_usage_gb,
            disk_usage_percent=disk_usage_percent,
            temperatura_celsius=temperatura_celsius,
            created_at=datetime.utcnow() # Ensure created_at is set
        )
        db.add(new_telemetry)
        db.commit()
        db.refresh(new_telemetry)

        # Optionally, update the last_telemetry_at in the JetsonNano table
        jetson_exists.last_telemetry_at = datetime.utcnow()
        db.commit() # Commit the update to JetsonNano as well
        db.refresh(jetson_exists)

        logger.info(f"Telemetry record created for Jetson {id_hardware_jetson} at {timestamp_telemetry}.")
        return new_telemetry

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError when creating telemetry for {id_hardware_jetson}: {e.orig}", exc_info=True)
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"SQLAlchemyError when creating telemetry for {id_hardware_jetson}: {e}", exc_info=True)
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating telemetry for {id_hardware_jetson}: {e}", exc_info=True)
        return None

