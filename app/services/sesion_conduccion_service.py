# app/services/sesion_conduccion_service.py
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid 

from sqlalchemy.orm import Session 

# Importar las operaciones CRUD específicas
from app.crud.crud_sesion_conduccion import sesion_conduccion_crud
from app.crud.crud_conductor import conductor_crud
from app.crud.crud_bus import bus_crud
# Importar los modelos para tipado
from app.models_db.cloud_database_models import SesionConduccion, Conductor, Bus 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class SesionConduccionService:
    """
    Capa de servicio para gestionar la lógica de negocio relacionada con las Sesiones de Conducción.
    Procesa los datos de sesión que llegan de la Jetson Nano.
    """

    def process_incoming_session_data(self, db: Session, session_data: Dict[str, Any]) -> Optional[SesionConduccion]:
        """
        Procesa los datos de sesión de conducción enviados por la Jetson Nano.
        Si la sesión ya existe (por id_sesion_conduccion_jetson), la actualiza (ej. con fecha_fin_real).
        Si no existe, crea una nueva sesión.

        Args:
            db (Session): La sesión de la base de datos.
            session_data (Dict[str, Any]): Diccionario con los datos de la sesión (de la Jetson Nano).
                                          Esperado: id_sesion_conduccion_jetson (str UUID),
                                                    id_conductor (str UUID), id_bus (str UUID),
                                                    fecha_inicio_real (str ISO),
                                                    fecha_fin_real (str ISO, opcional),
                                                    estado_sesion (str), etc.

        Returns:
            Optional[SesionConduccion]: El objeto SesionConduccion creado o actualizado, o None si falla.
        """
        jetson_session_id = session_data.get('id_sesion_conduccion_jetson')
        if not jetson_session_id:
            logger.warning("Fallo al procesar datos de sesión: 'id_sesion_conduccion_jetson' es requerido.")
            return None
        
        # Convertir id_sesion_conduccion_jetson a UUID si viene como string
        if isinstance(jetson_session_id, str):
            try:
                jetson_session_id = uuid.UUID(jetson_session_id)
                session_data['id_sesion_conduccion_jetson'] = jetson_session_id
            except ValueError:
                logger.warning(f"Fallo al procesar sesión: id_sesion_conduccion_jetson '{jetson_session_id}' no es un UUID válido.")
                return None

        logger.info(f"Procesando datos de sesión con ID de Jetson: {jetson_session_id}")

        # 1. Validar existencia del Conductor
        conductor_id = session_data.get('id_conductor')
        if not conductor_id:
            logger.warning(f"Fallo al procesar sesión {jetson_session_id}: id_conductor es requerido.")
            return None
        if isinstance(conductor_id, str):
            try: conductor_id = uuid.UUID(conductor_id)
            except ValueError: logger.warning(f"ID de conductor '{conductor_id}' no es UUID válido."); return None
        conductor_existente: Optional[Conductor] = conductor_crud.get(db, conductor_id)
        if not conductor_existente:
            logger.warning(f"Fallo al procesar sesión {jetson_session_id}: Conductor con ID '{conductor_id}' no existe.")
            return None
        session_data['id_conductor'] = conductor_id # Asegurar que sea UUID para el CRUD

        # 2. Validar existencia del Bus
        bus_id = session_data.get('id_bus')
        if not bus_id:
            logger.warning(f"Fallo al procesar sesión {jetson_session_id}: id_bus es requerido.")
            return None
        if isinstance(bus_id, str):
            try: bus_id = uuid.UUID(bus_id)
            except ValueError: logger.warning(f"ID de bus '{bus_id}' no es UUID válido."); return None
        bus_existente: Optional[Bus] = bus_crud.get(db, bus_id)
        if not bus_existente:
            logger.warning(f"Fallo al procesar sesión {jetson_session_id}: Bus con ID '{bus_id}' no existe.")
            return None
        session_data['id_bus'] = bus_id # Asegurar que sea UUID para el CRUD

        try:
            # Usar create_or_update para manejar tanto la creación como la actualización de la sesión
            # La clave única será 'id_sesion_conduccion_jetson'
            session_obj = sesion_conduccion_crud.create_or_update(db, session_data, unique_field='id_sesion_conduccion_jetson')
            
            logger.info(f"Sesión de conducción '{session_obj.id_sesion_conduccion_jetson}' procesada exitosamente. Estado: {session_obj.estado_sesion}.")
            return session_obj
        except Exception as e:
            logger.error(f"Error al procesar sesión '{jetson_session_id}': {e}", exc_info=True)
            db.rollback() 
            return None

    def get_sesion_details(self, db: Session, sesion_id: uuid.UUID) -> Optional[SesionConduccion]:
        """
        Recupera los detalles de una sesión de conducción específica por su ID primario de la nube.
        """
        logger.info(f"Obteniendo detalles para sesión de conducción ID: {sesion_id}")
        sesion = sesion_conduccion_crud.get(db, sesion_id)
        if not sesion:
            logger.warning(f"Sesión de conducción con ID '{sesion_id}' no encontrada.")
        return sesion

    def get_sesion_by_jetson_id(self, db: Session, jetson_session_id: uuid.UUID) -> Optional[SesionConduccion]:
        """
        Recupera los detalles de una sesión de conducción por su ID generado en la Jetson Nano.
        """
        logger.info(f"Obteniendo detalles para sesión de Jetson ID: {jetson_session_id}")
        sesion = sesion_conduccion_crud.get_by_jetson_session_id(db, jetson_session_id)
        if not sesion:
            logger.warning(f"Sesión de Jetson ID '{jetson_session_id}' no encontrada.")
        return sesion

    def get_active_sessions(self, db: Session, skip: int = 0, limit: int = 100) -> List[SesionConduccion]:
        """
        Recupera una lista de todas las sesiones de conducción activas.
        """
        logger.info(f"Obteniendo sesiones activas (skip={skip}, limit={limit}).")
        return sesion_conduccion_crud.get_multi(db, skip=skip, limit=limit, estado_sesion='Activa', fecha_fin_real=None)
    
    def get_sessions_by_bus(self, db: Session, bus_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[SesionConduccion]:
        """
        Recupera una lista de sesiones de conducción para un bus específico.
        """
        logger.info(f"Obteniendo sesiones para bus ID: {bus_id} (skip={skip}, limit={limit}).")
        bus_existente = bus_crud.get(db, bus_id)
        if not bus_existente:
            logger.warning(f"Bus con ID '{bus_id}' no encontrado. No se pueden obtener sus sesiones.")
            return []
        return sesion_conduccion_crud.get_sessions_by_bus(db, bus_id, skip=skip, limit=limit)

    def get_sessions_by_conductor(self, db: Session, conductor_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[SesionConduccion]:
        """
        Recupera una lista de sesiones de conducción para un conductor específico.
        """
        logger.info(f"Obteniendo sesiones para conductor ID: {conductor_id} (skip={skip}, limit={limit}).")
        conductor_existente = conductor_crud.get(db, conductor_id)
        if not conductor_existente:
            logger.warning(f"Conductor con ID '{conductor_id}' no encontrado. No se pueden obtener sus sesiones.")
            return []
        return sesion_conduccion_crud.get_sessions_by_conductor(db, conductor_id, skip=skip, limit=limit)


    def update_sesion_details(self, db: Session, sesion_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[SesionConduccion]:
        """
        Actualiza los detalles de una sesión de conducción existente por su ID primario de la nube.
        """
        logger.info(f"Intentando actualizar sesión de conducción ID: {sesion_id}")
        sesion_existente: Optional[SesionConduccion] = sesion_conduccion_crud.get(db, sesion_id)
        if not sesion_existente:
            logger.warning(f"No se puede actualizar: Sesión de conducción con ID '{sesion_id}' no encontrada.")
            return None
        
        # Validar si se intentan cambiar conductor o bus (solo si es necesario, suelen ser inmutables en sesión)
        if 'id_conductor' in updates:
            new_conductor_id = updates['id_conductor']
            if isinstance(new_conductor_id, str):
                try: new_conductor_id = uuid.UUID(new_conductor_id)
                except ValueError: return None
            if not conductor_crud.get(db, new_conductor_id):
                logger.warning(f"Fallo al actualizar sesión: Nuevo conductor con ID '{new_conductor_id}' no existe.")
                return None
        
        if 'id_bus' in updates:
            new_bus_id = updates['id_bus']
            if isinstance(new_bus_id, str):
                try: new_bus_id = uuid.UUID(new_bus_id)
                except ValueError: return None
            if not bus_crud.get(db, new_bus_id):
                logger.warning(f"Fallo al actualizar sesión: Nuevo bus con ID '{new_bus_id}' no existe.")
                return None
        
        try:
            updated_sesion = sesion_conduccion_crud.update(db, sesion_existente, updates)
            logger.info(f"Sesión de conducción ID '{sesion_id}' actualizada exitosamente.")
            return updated_sesion
        except Exception as e:
            logger.error(f"Error actualizando sesión de conducción ID '{sesion_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def delete_sesion(self, db: Session, sesion_id: uuid.UUID) -> bool:
        """
        Elimina una sesión de conducción del sistema.
        Normalmente, las sesiones no se eliminan, solo se marcan como 'Finalizada' o 'Inactiva'.
        """
        logger.info(f"Intentando eliminar sesión de conducción ID: {sesion_id}")
        sesion_to_delete = sesion_conduccion_crud.get(db, sesion_id)
        if not sesion_to_delete:
            logger.warning(f"No se pudo eliminar: Sesión de conducción con ID '{sesion_id}' no encontrada.")
            return False
        
        try:
            deleted_sesion = sesion_conduccion_crud.remove(db, sesion_id)
            if deleted_sesion:
                logger.info(f"Sesión de conducción ID '{sesion_id}' eliminada exitosamente.")
                return True
            else:
                return False 
        except Exception as e:
            logger.error(f"Error eliminando sesión de conducción ID '{sesion_id}': {e}", exc_info=True)
            db.rollback()
            return False

# Crea una instancia de SesionConduccionService para ser utilizada por los endpoints API.
sesion_conduccion_service = SesionConduccionService()