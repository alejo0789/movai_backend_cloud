# app/services/asignacion_programada_service.py
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import uuid 

from sqlalchemy.orm import Session 

# Importar las operaciones CRUD específicas
from app.crud.crud_asignacion_programada import asignacion_programada_crud
from app.crud.crud_conductor import conductor_crud
from app.crud.crud_bus import bus_crud
# Importar los modelos para tipado
from app.models_db.cloud_database_models import AsignacionProgramada, Conductor, Bus 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class AsignacionProgramadaService:
    """
    Capa de servicio para gestionar la lógica de negocio relacionada con las Asignaciones Programadas.
    Interactúa con la capa CRUD para realizar operaciones de base de datos y validaciones de negocio.
    """

    def create_new_asignacion_programada(self, db: Session, asignacion_data: Dict[str, Any]) -> Optional[AsignacionProgramada]:
        """
        Crea una nueva asignación programada en el sistema.
        Realiza validaciones de negocio como verificar la existencia del conductor y el bus.

        Args:
            db (Session): La sesión de la base de datos.
            asignacion_data (Dict[str, Any]): Diccionario que contiene los datos de la asignación (ej. id_conductor, id_bus, fechas).

        Returns:
            Optional[AsignacionProgramada]: El objeto AsignacionProgramada recién creado, o None si la validación falla.
        """
        logger.info(f"Intentando crear nueva asignación programada para bus {asignacion_data.get('id_bus')} y conductor {asignacion_data.get('id_conductor')}")

        # Validar existencia de Conductor
        conductor_id = asignacion_data.get('id_conductor')
        if not conductor_id:
            logger.warning("Fallo al crear asignación: id_conductor es requerido.")
            return None
        if isinstance(conductor_id, str):
            try: conductor_id = uuid.UUID(conductor_id)
            except ValueError: return None
        conductor_existente: Optional[Conductor] = conductor_crud.get(db, conductor_id)
        if not conductor_existente:
            logger.warning(f"Fallo al crear asignación: Conductor con ID '{conductor_id}' no existe.")
            return None
        
        # Validar existencia de Bus
        bus_id = asignacion_data.get('id_bus')
        if not bus_id:
            logger.warning("Fallo al crear asignación: id_bus es requerido.")
            return None
        if isinstance(bus_id, str):
            try: bus_id = uuid.UUID(bus_id)
            except ValueError: return None
        bus_existente: Optional[Bus] = bus_crud.get(db, bus_id)
        if not bus_existente:
            logger.warning(f"Fallo al crear asignación: Bus con ID '{bus_id}' no existe.")
            return None

        # Opcional: Validar que las fechas sean lógicas (fecha_inicio <= fecha_fin)
        fecha_inicio = asignacion_data.get('fecha_inicio_programada')
        fecha_fin = asignacion_data.get('fecha_fin_programada')
        if fecha_inicio and fecha_fin and isinstance(fecha_inicio, str) and isinstance(fecha_fin, str):
            try:
                dt_inicio = datetime.fromisoformat(fecha_inicio)
                dt_fin = datetime.fromisoformat(fecha_fin)
                if dt_inicio > dt_fin:
                    logger.warning("Fallo al crear asignación: La fecha de inicio no puede ser posterior a la fecha de fin.")
                    return None
            except ValueError:
                logger.warning("Fallo al crear asignación: Formato de fecha(s) inválido.")
                return None
        
        try:
            new_asignacion = asignacion_programada_crud.create(db, asignacion_data)
            logger.info(f"Asignación programada (ID: {new_asignacion.id}) creada exitosamente: Conductor='{conductor_existente.nombre_completo}', Bus='{bus_existente.placa}'.")
            return new_asignacion
        except Exception as e:
            logger.error(f"Error creando asignación programada: {e}", exc_info=True)
            db.rollback() 
            return None

    def get_asignacion_details(self, db: Session, asignacion_id: uuid.UUID) -> Optional[AsignacionProgramada]:
        """
        Recupera los detalles de una asignación programada específica por su ID.
        """
        logger.info(f"Obteniendo detalles para asignación programada ID: {asignacion_id}")
        asignacion = asignacion_programada_crud.get(db, asignacion_id)
        if not asignacion:
            logger.warning(f"Asignación programada con ID '{asignacion_id}' no encontrada.")
        return asignacion
    
    def get_all_asignaciones_programadas(self, db: Session, skip: int = 0, limit: int = 100,
                                         id_bus: Optional[uuid.UUID] = None, # <<<<<<<<<<<<< NUEVO PARAMETRO
                                         id_conductor: Optional[uuid.UUID] = None # <<<<<<<<<<<<< NUEVO PARAMETRO
                                         ) -> List[AsignacionProgramada]:
        """
        Recupera una lista de todas las asignaciones programadas con paginación y filtrado opcional.
        """
        logger.info(f"Obteniendo asignaciones programadas (skip={skip}, limit={limit}, bus_id={id_bus}, conductor_id={id_conductor}).")
        # Ahora el CRUD puede manejar directamente el filtrado
        return asignacion_programada_crud.get_multi(db, skip=skip, limit=limit, id_bus=id_bus, id_conductor=id_conductor)
    
    def get_active_assignments_for_bus_api(self, db: Session, bus_id: uuid.UUID) -> List[AsignacionProgramada]:
        """
        Recupera las asignaciones programadas actualmente activas para un bus,
        útil para que la Jetson Nano pueda consultar qué conductores están previstos.
        """
        logger.info(f"Obteniendo asignaciones activas para bus ID: {bus_id}")
        bus_existente = bus_crud.get(db, bus_id)
        if not bus_existente:
            logger.warning(f"Bus con ID '{bus_id}' no encontrado. No se pueden obtener asignaciones.")
            return []
        
        return asignacion_programada_crud.get_active_assignments_for_bus(db, bus_id)

    def get_active_assignments_for_conductor_api(self, db: Session, conductor_id: uuid.UUID) -> List[AsignacionProgramada]:
        """
        Recupera las asignaciones programadas actualmente activas para un conductor.
        """
        logger.info(f"Obteniendo asignaciones activas para conductor ID: {conductor_id}")
        conductor_existente = conductor_crud.get(db, conductor_id)
        if not conductor_existente:
            logger.warning(f"Conductor con ID '{conductor_id}' no encontrado. No se pueden obtener asignaciones.")
            return []
        return asignacion_programada_crud.get_active_assignments_for_conductor(db, conductor_id)

    def update_asignacion_programada_details(self, db: Session, asignacion_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[AsignacionProgramada]:
        """
        Actualiza los detalles de una asignación programada existente.
        """
        logger.info(f"Intentando actualizar asignación programada ID: {asignacion_id}")
        asignacion_existente: Optional[AsignacionProgramada] = asignacion_programada_crud.get(db, asignacion_id)
        if not asignacion_existente:
            logger.warning(f"No se puede actualizar: Asignación programada con ID '{asignacion_id}' no encontrada.")
            return None
        
        # Validar existencia de Conductor si se intenta cambiar
        if 'id_conductor' in updates:
            new_conductor_id = updates['id_conductor']
            if isinstance(new_conductor_id, str):
                try: new_conductor_id = uuid.UUID(new_conductor_id)
                except ValueError: return None
            if not conductor_crud.get(db, new_conductor_id):
                logger.warning(f"Fallo al actualizar asignación: Nuevo conductor con ID '{new_conductor_id}' no existe.")
                return None
        
        # Validar existencia de Bus si se intenta cambiar
        if 'id_bus' in updates:
            new_bus_id = updates['id_bus']
            if isinstance(new_bus_id, str):
                try: new_bus_id = uuid.UUID(new_bus_id)
                except ValueError: return None
            if not bus_crud.get(db, new_bus_id):
                logger.warning(f"Fallo al actualizar asignación: Nuevo bus con ID '{new_bus_id}' no existe.")
                return None
        
        # Validar fechas si se actualizan
        fecha_inicio_str = updates.get('fecha_inicio_programada')
        fecha_fin_str = updates.get('fecha_fin_programada')
        
        # Usar las fechas existentes si no se proporcionan en la actualización
        dt_inicio = datetime.fromisoformat(fecha_inicio_str) if fecha_inicio_str else asignacion_existente.fecha_inicio_programada
        dt_fin = datetime.fromisoformat(fecha_fin_str) if fecha_fin_str else asignacion_existente.fecha_fin_programada
        
        if dt_inicio and dt_fin and dt_inicio > dt_fin:
            logger.warning("Fallo al actualizar asignación: La fecha de inicio no puede ser posterior a la fecha de fin.")
            return None
        
        try:
            updated_asignacion = asignacion_programada_crud.update(db, asignacion_existente, updates)
            logger.info(f"Asignación programada ID '{asignacion_id}' actualizada exitosamente.")
            return updated_asignacion
        except Exception as e:
            logger.error(f"Error actualizando asignación programada ID '{asignacion_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def delete_asignacion_programada(self, db: Session, asignacion_id: uuid.UUID) -> bool:
        """
        Elimina una asignación programada del sistema.
        """
        logger.info(f"Intentando eliminar asignación programada ID: {asignacion_id}")
        asignacion_to_delete = asignacion_programada_crud.get(db, asignacion_id)
        if not asignacion_to_delete:
            logger.warning(f"No se pudo eliminar: Asignación programada con ID '{asignacion_id}' no encontrada.")
            return False
        
        try:
            deleted_asignacion = asignacion_programada_crud.remove(db, asignacion_id)
            if deleted_asignacion:
                logger.info(f"Asignación programada ID '{asignacion_id}' eliminada exitosamente.")
                return True
            else:
                return False 
        except Exception as e:
            logger.error(f"Error eliminando asignación programada ID '{asignacion_id}': {e}", exc_info=True)
            db.rollback()
            return False

# Crea una instancia de AsignacionProgramadaService para ser utilizada por los endpoints API.
asignacion_programada_service = AsignacionProgramadaService()