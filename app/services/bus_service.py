# app/services/bus_service.py
import logging
from typing import Optional, Dict, Any, List
import uuid 

from sqlalchemy.orm import Session 

# Importar las operaciones CRUD específicas para Bus y Empresa
from app.crud.crud_bus import bus_crud
from app.crud.crud_empresa import empresa_crud # Necesario para verificar que la empresa existe
# Importar el modelo Bus para tipado
from app.models_db.cloud_database_models import Bus, Empresa 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class BusService:
    """
    Capa de servicio para gestionar la lógica de negocio relacionada con los Buses.
    Interactúa con la capa CRUD para realizar operaciones de base de datos.
    """

    def register_new_bus(self, db: Session, bus_data: Dict[str, Any]) -> Optional[Bus]:
        """
        Registra un nuevo bus en el sistema.
        Realiza validaciones de negocio como verificar la existencia de la empresa asociada
        y la unicidad de la placa.

        Args:
            db (Session): La sesión de la base de datos.
            bus_data (Dict[str, Any]): Diccionario que contiene los datos del bus (ej. placa, id_empresa).

        Returns:
            Optional[Bus]: El objeto Bus recién creado, o None si la validación falla.
        """
        logger.info(f"Intentando registrar nuevo bus con placa: {bus_data.get('placa')}")

        # Validar que la empresa a la que se asocia el bus existe
        empresa_id = bus_data.get('id_empresa')
        if not empresa_id:
            logger.warning("Fallo al registrar bus: id_empresa es requerido.")
            return None
        
        # Asegurar que id_empresa es un UUID si viene como string
        if isinstance(empresa_id, str):
            try:
                empresa_id = uuid.UUID(empresa_id)
                bus_data['id_empresa'] = empresa_id # Actualizar el dict para el CRUD
            except ValueError:
                logger.warning(f"Fallo al registrar bus: id_empresa '{empresa_id}' no es un UUID válido.")
                return None

        empresa_existente: Optional[Empresa] = empresa_crud.get(db, empresa_id)
        if not empresa_existente:
            logger.warning(f"Fallo al registrar bus: La empresa con ID '{empresa_id}' no existe.")
            return None
        
        # Validar unicidad de la placa (aunque la BD lo fuerza, se valida antes para mejor UX)
        existing_bus_by_placa: Optional[Bus] = bus_crud.get_by_placa(db, bus_data.get('placa'))
        if existing_bus_by_placa:
            logger.warning(f"Fallo al registrar bus: La placa '{bus_data.get('placa')}' ya existe.")
            return None
        
        try:
            # Crear el bus utilizando la operación CRUD
            new_bus = bus_crud.create(db, bus_data)
            logger.info(f"Bus '{new_bus.placa}' (ID: {new_bus.id}) registrado exitosamente para la empresa '{empresa_existente.nombre_empresa}'.")
            return new_bus
        except Exception as e:
            logger.error(f"Error registrando bus '{bus_data.get('placa')}': {e}", exc_info=True)
            db.rollback() 
            return None

    def get_bus_details(self, db: Session, bus_id: uuid.UUID) -> Optional[Bus]:
        """
        Recupera los detalles de un bus específico por su ID.
        """
        logger.info(f"Obteniendo detalles para el bus ID: {bus_id}")
        bus = bus_crud.get(db, bus_id)
        if not bus:
            logger.warning(f"Bus con ID '{bus_id}' no encontrado.")
        return bus

    def get_bus_by_placa_logic(self, db: Session, placa: str) -> Optional[Bus]:
        """
        Recupera los detalles de un bus por su placa.
        Este método será utilizado por la Jetson Nano para obtener la información del bus.
        """
        logger.info(f"Obteniendo detalles para el bus con placa: {placa}")
        bus = bus_crud.get_by_placa(db, placa)
        if not bus:
            logger.warning(f"Bus con placa '{placa}' no encontrado.")
        return bus

    def get_all_buses(self, db: Session, skip: int = 0, limit: int = 100) -> List[Bus]:
        """
        Recupera una lista de todos los buses con paginación.
        """
        logger.info(f"Obteniendo todos los buses (skip={skip}, limit={limit}).")
        return bus_crud.get_multi(db, skip=skip, limit=limit)
    
    def get_buses_by_empresa(self, db: Session, empresa_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Bus]:
        """
        Recupera una lista de buses asociados a una empresa específica.
        """
        logger.info(f"Obteniendo buses para la empresa ID: {empresa_id} (skip={skip}, limit={limit}).")
        empresa_existente = empresa_crud.get(db, empresa_id)
        if not empresa_existente:
            logger.warning(f"Empresa con ID '{empresa_id}' no encontrada. No se pueden obtener sus buses.")
            return []
        return bus_crud.get_buses_by_empresa(db, empresa_id, skip=skip, limit=limit)

    def update_bus_details(self, db: Session, bus_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[Bus]:
        """
        Actualiza los detalles de un bus existente.
        """
        logger.info(f"Intentando actualizar bus ID: {bus_id}")
        bus_existente: Optional[Bus] = bus_crud.get(db, bus_id)
        if not bus_existente:
            logger.warning(f"No se puede actualizar: Bus con ID '{bus_id}' no encontrado.")
            return None
        
        # Si se intenta cambiar la empresa, validar que la nueva empresa exista
        if 'id_empresa' in updates:
            new_empresa_id = updates['id_empresa']
            if isinstance(new_empresa_id, str):
                try:
                    new_empresa_id = uuid.UUID(new_empresa_id)
                    updates['id_empresa'] = new_empresa_id
                except ValueError:
                    logger.warning(f"Fallo al actualizar bus: Nuevo id_empresa '{updates['id_empresa']}' no es un UUID válido.")
                    return None
            
            if not empresa_crud.get(db, new_empresa_id):
                logger.warning(f"Fallo al actualizar bus: La nueva empresa con ID '{new_empresa_id}' no existe.")
                return None
        
        # Validar unicidad de la placa si se intenta cambiar
        if 'placa' in updates and updates['placa'] != bus_existente.placa:
            existing_bus_by_placa = bus_crud.get_by_placa(db, updates['placa'])
            if existing_bus_by_placa and existing_bus_by_placa.id != bus_id:
                logger.warning(f"Fallo al actualizar bus: La placa '{updates['placa']}' ya está en uso por otro bus.")
                return None

        try:
            updated_bus = bus_crud.update(db, bus_existente, updates)
            logger.info(f"Bus '{bus_existente.placa}' (ID: {bus_id}) actualizado exitosamente.")
            return updated_bus
        except Exception as e:
            logger.error(f"Error actualizando bus ID '{bus_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def delete_bus(self, db: Session, bus_id: uuid.UUID) -> bool:
        """
        Elimina un bus del sistema.
        Debería considerar las implicaciones de FK (eventos, asignaciones, etc.).
        """
        logger.info(f"Intentando eliminar bus ID: {bus_id}")
        # En un sistema real, es crucial manejar esto con cuidado:
        # - Desactivar el bus en lugar de eliminarlo (soft delete).
        # - Si se elimina, asegurar que no haya datos transaccionales (eventos, sesiones)
        #   vinculados o que estos también sean eliminados en cascada (requiere configuración en el modelo).
        
        # Para el prototipo, la eliminación directa fallará si hay FKs referenciando este bus.
        # En producción, se preferiría una eliminación lógica (cambiar 'estado_operativo' a 'Inactivo').
        
        bus_to_delete = bus_crud.get(db, bus_id)
        if not bus_to_delete:
            logger.warning(f"No se pudo eliminar: Bus con ID '{bus_id}' no encontrado.")
            return False
        
        try:
            # Aquí podrías verificar relaciones activas si no confías en las FK de la DB
            # if bus_to_delete.eventos or bus_to_delete.sesiones_conduccion:
            #     logger.warning(f"No se puede eliminar el bus {bus_id} porque tiene eventos o sesiones asociados.")
            #     return False

            deleted_bus = bus_crud.remove(db, bus_id)
            if deleted_bus:
                logger.info(f"Bus ID '{bus_id}' eliminado exitosamente.")
                return True
            else:
                return False # Debería ser atrapado por el not bus_to_delete
        except Exception as e:
            logger.error(f"Error eliminando bus ID '{bus_id}': {e}", exc_info=True)
            db.rollback()
            return False

# Crea una instancia de BusService para ser utilizada por los endpoints API.
bus_service = BusService()