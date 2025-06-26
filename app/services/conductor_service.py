# app/services/conductor_service.py
import logging
from typing import Optional, Dict, Any, List
import uuid 
import qrcode # <<<<<<<<<<<<<<<< IMPORTADO
import io # Para manejar la imagen en memoria
from PIL import Image # Para manipular la imagen del QR

from sqlalchemy.orm import Session 

# Importar las operaciones CRUD específicas
from app.crud.crud_conductor import conductor_crud
from app.crud.crud_empresa import empresa_crud 
from app.crud.crud_bus import bus_crud 
from app.crud.crud_asignacion_programada import asignacion_programada_crud 

# Importar los modelos para tipado
from app.models_db.cloud_database_models import Conductor, Empresa, Bus, AsignacionProgramada 

# Configuración del logger para este módulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class ConductorService:
    """
    Capa de servicio para gestionar la lógica de negocio relacionada con los Conductores.
    Interactúa con la capa CRUD para realizar operaciones de base de datos.
    """

    def register_new_conductor(self, db: Session, conductor_data: Dict[str, Any]) -> Optional[Conductor]:
        """
        Registra un nuevo conductor en el sistema.
        Realiza validaciones de negocio como verificar la existencia de la empresa asociada
        y la unicidad de la cédula.

        Args:
            db (Session): La sesión de la base de datos.
            conductor_data (Dict[str, Any]): Diccionario que contiene los datos del conductor (ej. cédula, nombre, id_empresa).

        Returns:
            Optional[Conductor]: El objeto Conductor recién creado, o None si la validación falla.
        """
        logger.info(f"Intentando registrar nuevo conductor: {conductor_data.get('nombre_completo')} con cédula {conductor_data.get('cedula')}")

        empresa_id = conductor_data.get('id_empresa')
        if not empresa_id:
            logger.warning("Fallo al registrar conductor: id_empresa es requerido.")
            return None
        
        if isinstance(empresa_id, str):
            try:
                empresa_id = uuid.UUID(empresa_id)
                conductor_data['id_empresa'] = empresa_id 
            except ValueError:
                logger.warning(f"Fallo al registrar conductor: id_empresa '{empresa_id}' no es un UUID válido.")
                return None

        empresa_existente: Optional[Empresa] = empresa_crud.get(db, empresa_id)
        if not empresa_existente:
            logger.warning(f"Fallo al registrar conductor: La empresa con ID '{empresa_id}' no existe.")
            return None
        
        existing_conductor_by_cedula: Optional[Conductor] = conductor_crud.get_by_cedula(db, conductor_data.get('cedula'))
        if existing_conductor_by_cedula:
            logger.warning(f"Fallo al registrar conductor: La cédula '{conductor_data.get('cedula')}' ya existe.")
            return None
        
        # Opcional: Generar código QR hash si no se proporciona (ej. hash(cedula) o usar la cédula directamente)
        # Esto es importante para la lógica de Jetson Nano que usa el hash del QR
        if 'codigo_qr_hash' not in conductor_data or not conductor_data['codigo_qr_hash']:
            conductor_data['codigo_qr_hash'] = conductor_data.get('cedula') 

        try:
            new_conductor = conductor_crud.create(db, conductor_data)
            logger.info(f"Conductor '{new_conductor.nombre_completo}' (ID: {new_conductor.id}) registrado exitosamente para la empresa '{empresa_existente.nombre_empresa}'.")
            return new_conductor
        except Exception as e:
            logger.error(f"Error registrando conductor '{conductor_data.get('nombre_completo')}': {e}", exc_info=True)
            db.rollback() 
            return None

    def get_conductor_details(self, db: Session, conductor_id: uuid.UUID) -> Optional[Conductor]:
        """
        Recupera los detalles de un conductor específico por su ID.
        """
        logger.info(f"Obteniendo detalles para el conductor ID: {conductor_id}")
        conductor = conductor_crud.get(db, conductor_id)
        if not conductor:
            logger.warning(f"Conductor con ID '{conductor_id}' no encontrado.")
        return conductor
    
    def get_conductor_by_cedula_logic(self, db: Session, cedula: str) -> Optional[Conductor]:
        """
        Recupera los detalles de un conductor por su cédula.
        """
        logger.info(f"Obteniendo detalles para el conductor con cédula: {cedula}")
        conductor = conductor_crud.get_by_cedula(db, cedula)
        if not conductor:
            logger.warning(f"Conductor con cédula '{cedula}' no encontrado.")
        return conductor

    def get_all_conductores(self, db: Session, skip: int = 0, limit: int = 100) -> List[Conductor]:
        """
        Recupera una lista de todos los conductores con paginación.
        """
        logger.info(f"Obteniendo todos los conductores (skip={skip}, limit={limit}).")
        return conductor_crud.get_multi(db, skip=skip, limit=limit)
    
    def get_conductores_by_empresa(self, db: Session, empresa_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conductor]:
        """
        Recupera una lista de conductores asociados a una empresa específica.
        """
        logger.info(f"Obteniendo conductores para la empresa ID: {empresa_id} (skip={skip}, limit={limit}).")
        empresa_existente = empresa_crud.get(db, empresa_id)
        if not empresa_existente:
            logger.warning(f"Empresa con ID '{empresa_id}' no encontrada. No se pueden obtener sus conductores.")
            return []
        return conductor_crud.get_conductores_by_empresa(db, empresa_id, skip=skip, limit=limit)

    def get_conductores_by_bus(self, db: Session, bus_id: uuid.UUID) -> List[Conductor]:
        """
        Obtiene una lista de TODOS los conductores que alguna vez han sido
        asignados (programados) para manejar un bus específico, sin importar
        si la asignación está activa o si la fecha de fin ya pasó.
        """
        logger.info(f"Obteniendo TODOS los conductores programados para el bus ID: {bus_id}")
        
        bus_existente: Optional[Bus] = bus_crud.get(db, bus_id)
        if not bus_existente:
            logger.warning(f"Bus con ID '{bus_id}' no encontrado. No se pueden obtener sus conductores programados.")
            return []

        all_assignments_for_bus: List[AsignacionProgramada] = asignacion_programada_crud.get_multi(db, id_bus=bus_id)
        
        if not all_assignments_for_bus:
            logger.info(f"No se encontraron asignaciones programadas (activas o no) para el bus {bus_id}.")
            return []

        unique_conductor_ids: set[uuid.UUID] = {assignment.id_conductor for assignment in all_assignments_for_bus}
        
        conductores: List[Conductor] = conductor_crud.get_multi_by_ids(db, list(unique_conductor_ids))
        
        logger.info(f"Encontrados {len(conductores)} conductores (históricos/actuales) programados para el bus {bus_id}.")
        return conductores


    def update_conductor_details(self, db: Session, conductor_id: uuid.UUID, updates: Dict[str, Any]) -> Optional[Conductor]:
        """
        Actualiza los detalles de un conductor existente.
        """
        logger.info(f"Intentando actualizar conductor ID: {conductor_id}")
        conductor_existente: Optional[Conductor] = conductor_crud.get(db, conductor_id)
        if not conductor_existente:
            logger.warning(f"No se puede actualizar: Conductor con ID '{conductor_id}' no encontrado.")
            return None
        
        if 'id_empresa' in updates:
            new_empresa_id = updates['id_empresa']
            if isinstance(new_empresa_id, str):
                try:
                    new_empresa_id = uuid.UUID(new_empresa_id)
                    updates['id_empresa'] = new_empresa_id
                except ValueError:
                    logger.warning(f"Fallo al actualizar conductor: Nuevo id_empresa '{updates['id_empresa']}' no es un UUID válido.")
                    return None
            
            if not empresa_crud.get(db, new_empresa_id):
                logger.warning(f"Fallo al actualizar conductor: La nueva empresa con ID '{new_empresa_id}' no existe.")
                return None
        
        if 'cedula' in updates and updates['cedula'] != conductor_existente.cedula:
            existing_conductor_by_cedula = conductor_crud.get_by_cedula(db, updates['cedula'])
            if existing_conductor_by_cedula and existing_conductor_by_cedula.id != conductor_id:
                logger.warning(f"Fallo al actualizar conductor: La cédula '{updates['cedula']}' ya está en uso por otro conductor.")
                return None

        try:
            updated_conductor = conductor_crud.update(db, conductor_existente, updates)
            logger.info(f"Conductor '{conductor_existente.nombre_completo}' (ID: {conductor_id}) actualizado exitosamente.")
            return updated_conductor
        except Exception as e:
            logger.error(f"Error actualizando conductor ID '{conductor_id}': {e}", exc_info=True)
            db.rollback()
            return None

    def delete_conductor(self, db: Session, conductor_id: uuid.UUID) -> bool:
        """
        Elimina un conductor del sistema.
        Considera las implicaciones de FK (eventos, asignaciones, etc.).
        """
        logger.info(f"Intentando eliminar conductor ID: {conductor_id}")
        conductor_to_delete = conductor_crud.get(db, conductor_id)
        if not conductor_to_delete:
            logger.warning(f"No se pudo eliminar: Conductor con ID '{conductor_id}' no encontrado.")
            return False
        
        try:
            deleted_conductor = conductor_crud.remove(db, conductor_id)
            if deleted_conductor:
                logger.info(f"Conductor ID '{conductor_id}' eliminado exitosamente.")
                return True
            else:
                return False 
        except Exception as e:
            logger.error(f"Error eliminando conductor ID '{conductor_id}': {e}", exc_info=True)
            db.rollback()
            return False

    def generate_qr_code_for_conductor(self, db: Session, conductor_id: uuid.UUID, size: int = 10, border: int = 4) -> Optional[io.BytesIO]:
        """
        Genera un código QR para un conductor específico.
        El QR contendrá la cédula del conductor.
        
        Args:
            db (Session): Sesión de la base de datos.
            conductor_id (uuid.UUID): ID del conductor.
            size (int): Tamaño del QR (módulos, ej. 10 para 10x10).
            border (int): Ancho del borde blanco alrededor del QR.
            
        Returns:
            Optional[io.BytesIO]: Un objeto BytesIO que contiene la imagen PNG del QR, o None si el conductor no existe.
        """
        logger.info(f"Generando QR para conductor ID: {conductor_id}")
        conductor = self.get_conductor_details(db, conductor_id)
        if not conductor:
            logger.warning(f"No se puede generar QR: Conductor con ID '{conductor_id}' no encontrado.")
            return None
        
        # El dato del QR será la cédula del conductor
        qr_data = conductor.cedula
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L, # Nivel de corrección de errores
                box_size=size,
                border=border,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
            
            # Guardar la imagen en un buffer en memoria
            byte_io = io.BytesIO()
            img.save(byte_io, format='PNG')
            byte_io.seek(0) # Mover el cursor al inicio del buffer
            
            logger.info(f"QR generado para conductor {conductor.cedula}.")
            return byte_io
        except Exception as e:
            logger.error(f"Error generando QR para conductor {conductor_id}: {e}", exc_info=True)
            return None


# Crea una instancia de ConductorService para ser utilizada por los endpoints API.
conductor_service = ConductorService()